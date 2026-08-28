#include "training/environment/TankArena.h"

#include <cassert>
#include <cmath>

using TankTrouble::training::ArenaConfig;
using TankTrouble::training::TankAction;
using TankTrouble::training::TankArena;

int main()
{
    ArenaConfig config;
    config.maxDecisions = 1;
    TankArena first(config);
    TankArena second(config);
    const auto firstReset = first.reset(77);
    const auto secondReset = second.reset(77);
    assert(firstReset == secondReset);
    assert(static_cast<int>(firstReset.size()) == TankArena::OBSERVATION_SIZE);

    const TankAction simultaneous = {1, 2, 1};
    const auto firstStep = first.step(simultaneous);
    const auto secondStep = second.step(simultaneous);
    assert(firstStep.observation == secondStep.observation);
    assert(firstStep.reward == secondStep.reward);
    assert(firstStep.truncated);
    assert(std::isfinite(firstStep.reward));

    TankArena different(config);
    const auto differentReset = different.reset(78);
    assert(firstReset != differentReset);
    return 0;
}
