#include "training/environment/TankArena.h"

#include <cassert>
#include <cmath>
#include <vector>

using TankTrouble::training::ArenaConfig;
using TankTrouble::training::TankAction;
using TankTrouble::training::TankArena;

int main()
{
    ArenaConfig config;
    config.maxDecisions = 200;
    TankArena first(config);
    TankArena second(config);
    const auto firstReset = first.reset(77);
    const auto secondReset = second.reset(77);
    assert(firstReset == secondReset);
    assert(static_cast<int>(firstReset.size()) == TankArena::OBSERVATION_SIZE);

    const std::vector<TankAction> actions = {
        {1, 2, 1}, {1, 0, 0}, {0, 1, 0}, {2, 0, 0}, {1, 1, 0},
        {0, 0, 1}, {2, 2, 0}, {1, 0, 0}, {0, 2, 0}, {1, 1, 1},
    };
    for(int step = 0; step < config.maxDecisions; ++step)
    {
        const TankAction action = actions[static_cast<size_t>(step) % actions.size()];
        const auto firstStep = first.step(action);
        const auto secondStep = second.step(action);
        assert(firstStep.observation == secondStep.observation);
        assert(firstStep.reward == secondStep.reward);
        assert(firstStep.terminated == secondStep.terminated);
        assert(firstStep.truncated == secondStep.truncated);
        assert(firstStep.playerWon == secondStep.playerWon);
        assert(std::isfinite(firstStep.reward));
        if(firstStep.terminated || firstStep.truncated)
            break;
    }

    TankArena different(config);
    const auto differentReset = different.reset(78);
    assert(firstReset != differentReset);
    return 0;
}
