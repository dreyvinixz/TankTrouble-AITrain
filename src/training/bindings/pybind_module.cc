#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>

#include <stdexcept>
#include <vector>

#include "training/environment/TankArena.h"

namespace py = pybind11;
using TankTrouble::training::ArenaConfig;
using TankTrouble::training::StepResult;
using TankTrouble::training::TankAction;
using TankTrouble::training::TankArena;

namespace
{
    class VectorTankArena
    {
    public:
        VectorTankArena(int count, uint32_t seed, int ticksPerAction, int maxDecisions,
                        float winReward, float lossReward, float survivalReward,
                        float hitOpponentReward, float hitByOpponentReward): config_(), rootSeed_(seed)
        {
            if(count <= 0) throw std::invalid_argument("count must be positive");
            config_.seed = seed;
            config_.ticksPerAction = ticksPerAction;
            config_.maxDecisions = maxDecisions;
            config_.winReward = winReward;
            config_.lossReward = lossReward;
            config_.survivalRewardPerTick = survivalReward;
            config_.hitOpponentReward = hitOpponentReward;
            config_.hitByOpponentReward = hitByOpponentReward;
            environments_.reserve(static_cast<size_t>(count));
            for(int index = 0; index < count; ++index)
            {
                ArenaConfig localConfig = config_;
                localConfig.seed += static_cast<uint32_t>(index);
                environments_.emplace_back(localConfig);
            }
            episodeCounters_.assign(static_cast<size_t>(count), 0);
        }

        py::array_t<float> reset(uint32_t seed)
        {
            rootSeed_ = seed;
            py::array_t<float> output({static_cast<py::ssize_t>(environments_.size()),
                                       static_cast<py::ssize_t>(TankArena::OBSERVATION_SIZE)});
            auto view = output.mutable_unchecked<2>();
            for(size_t index = 0; index < environments_.size(); ++index)
            {
                episodeCounters_[index] = 0;
                const auto observation = environments_[index].reset(episodeSeed(index));
                for(size_t feature = 0; feature < observation.size(); ++feature)
                    view(static_cast<py::ssize_t>(index), static_cast<py::ssize_t>(feature)) = observation[feature];
            }
            return output;
        }

        py::tuple step(const py::array_t<int, py::array::c_style | py::array::forcecast>& actions)
        {
            if(actions.ndim() != 2 || actions.shape(0) != static_cast<py::ssize_t>(environments_.size()) || actions.shape(1) != 3)
                throw std::invalid_argument("actions must have shape [num_envs, 3]");
            const auto actionView = actions.unchecked<2>();
            py::array_t<float> observations({static_cast<py::ssize_t>(environments_.size()),
                                              static_cast<py::ssize_t>(TankArena::OBSERVATION_SIZE)});
            py::array_t<float> rewards(static_cast<py::ssize_t>(environments_.size()));
            py::array_t<uint8_t> terminated(static_cast<py::ssize_t>(environments_.size()));
            py::array_t<uint8_t> truncated(static_cast<py::ssize_t>(environments_.size()));
            auto observationView = observations.mutable_unchecked<2>();
            auto rewardView = rewards.mutable_unchecked<1>();
            auto terminatedView = terminated.mutable_unchecked<1>();
            auto truncatedView = truncated.mutable_unchecked<1>();

            for(size_t index = 0; index < environments_.size(); ++index)
            {
                const TankAction action = {static_cast<uint8_t>(actionView(index, 0)),
                                           static_cast<uint8_t>(actionView(index, 1)),
                                           static_cast<uint8_t>(actionView(index, 2))};
                const StepResult result = environments_[index].step(action);
                std::vector<float> observation = result.observation;
                if(result.terminated || result.truncated)
                {
                    ++episodeCounters_[index];
                    observation = environments_[index].reset(episodeSeed(index));
                }
                for(size_t feature = 0; feature < observation.size(); ++feature)
                    observationView(static_cast<py::ssize_t>(index), static_cast<py::ssize_t>(feature)) = observation[feature];
                rewardView(static_cast<py::ssize_t>(index)) = result.reward;
                terminatedView(static_cast<py::ssize_t>(index)) = result.terminated;
                truncatedView(static_cast<py::ssize_t>(index)) = result.truncated;
            }
            return py::make_tuple(observations, rewards, terminated, truncated);
        }

        [[nodiscard]] int size() const {return static_cast<int>(environments_.size());}

    private:
        [[nodiscard]] uint32_t episodeSeed(size_t index) const
        {
            return rootSeed_ + static_cast<uint32_t>(index * 1000003U) + episodeCounters_[index] * 7919U;
        }

        ArenaConfig config_;
        std::vector<TankArena> environments_;
        uint32_t rootSeed_;
        std::vector<uint32_t> episodeCounters_;
    };
}

PYBIND11_MODULE(tanktrain_env, module)
{
    module.doc() = "Deterministic vectorized TankTrouble AI Train environment";
    module.attr("OBSERVATION_SIZE") = TankArena::OBSERVATION_SIZE;
    py::class_<VectorTankArena>(module, "VectorTankArena")
        .def(py::init<int, uint32_t, int, int, float, float, float, float, float>(), py::arg("num_envs"), py::arg("seed"),
             py::arg("ticks_per_action") = 3, py::arg("max_decisions") = 600,
             py::arg("win_reward") = 1.0F, py::arg("loss_reward") = -1.0F,
             py::arg("survival_reward") = 0.002F, py::arg("hit_opponent_reward") = 0.10F,
             py::arg("hit_by_opponent_reward") = -0.10F)
        .def("reset", &VectorTankArena::reset, py::arg("seed"))
        .def("step", &VectorTankArena::step, py::arg("actions"))
        .def_property_readonly("num_envs", &VectorTankArena::size);
}
