#include "training/environment/TankArena.h"

#include <cassert>
#include <cmath>
#include <iostream>
#include <vector>

using TankTrouble::training::ArenaConfig;
using TankTrouble::training::StepResult;
using TankTrouble::training::TankAction;
using TankTrouble::training::TankArena;

void testDeterminism()
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
    std::cout << "[PASS] testDeterminism\n";
}

void testTimeoutReward()
{
    ArenaConfig config;
    config.maxDecisions = 5;
    config.survivalRewardPerTick = 0.0F;
    config.timeoutReward = -0.20F;
    TankArena arena(config);
    arena.reset(12345);

    StepResult lastResult;
    for(int step = 0; step < config.maxDecisions; ++step)
    {
        lastResult = arena.step({0, 0, 0});
        if(lastResult.terminated || lastResult.truncated)
            break;
    }

    if(!lastResult.terminated)
    {
        assert(lastResult.truncated);
        assert(std::abs(lastResult.reward - (-0.20F)) < 1e-5F);
    }
    std::cout << "[PASS] testTimeoutReward\n";
}

void testObservationContract()
{
    ArenaConfig config;
    TankArena arena(config);
    const auto obs = arena.reset(42);
    assert(static_cast<int>(obs.size()) == TankArena::OBSERVATION_SIZE);
    for(float val: obs)
    {
        assert(std::isfinite(val));
    }
    std::cout << "[PASS] testObservationContract\n";
}

void testPlayerNotHitByOwnShellAtSpawn()
{
    ArenaConfig config;
    TankArena arena(config);
    arena.reset(100);

    // Fire a shot while moving forward
    const auto step1 = arena.step({1, 0, 1});
    // The player should NOT die instantly from its own barrel spawn
    assert(!step1.terminated);

    // Step 2: continue moving forward behind the shell
    const auto step2 = arena.step({1, 0, 0});
    assert(!step2.terminated);

    std::cout << "[PASS] testPlayerNotHitByOwnShellAtSpawn\n";
}

void testShellOwnerFeatureInObservation()
{
    ArenaConfig config;
    TankArena arena(config);
    arena.reset(200);

    // Fire shell
    const auto result = arena.step({0, 0, 1});
    const auto& obs = result.observation;

    // Shell 0 starts at index 12 (after 12 tank features)
    // Feature index 16 is shell owner: +1.0 for Player, -1.0 for Opponent
    const float shellOwner = obs[12 + 4];
    const float shellActive = obs[12 + 6];

    assert(shellActive == 1.0F);
    assert(shellOwner == 1.0F); // +1.0 explicitly encodes player's own shell
    std::cout << "[PASS] testShellOwnerFeatureInObservation (Owner=+1.0 for player shell verified)\n";
}

int main()
{
    testDeterminism();
    testTimeoutReward();
    testObservationContract();
    testPlayerNotHitByOwnShellAtSpawn();
    testShellOwnerFeatureInObservation();
    std::cout << "All TankArena C++ tests (5/5) passed successfully!\n";
    return 0;
}
