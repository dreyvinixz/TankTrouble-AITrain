#ifndef TANK_TROUBLE_AI_TRAIN_TANK_ARENA_H
#define TANK_TROUBLE_AI_TRAIN_TANK_ARENA_H

#include <array>
#include <cstdint>
#include <random>
#include <vector>

namespace TankTrouble::training
{
    struct ArenaConfig
    {
        uint32_t seed = 17;
        int ticksPerAction = 3;
        int maxDecisions = 600;
        int maxShellsObserved = 8;
        float winReward = 1.0F;
        float lossReward = -1.0F;
        float survivalRewardPerTick = 0.002F;
        float hitOpponentReward = 0.10F;
        float hitByOpponentReward = -0.10F;
    };

    struct TankAction
    {
        // movement: 0 idle, 1 forward, 2 backward
        // rotation: 0 none, 1 clockwise, 2 counterclockwise
        // fire: 0 no request, 1 request
        uint8_t movement = 0;
        uint8_t rotation = 0;
        uint8_t fire = 0;
    };

    struct StepResult
    {
        std::vector<float> observation;
        float reward = 0.0F;
        bool terminated = false;
        bool truncated = false;
        bool playerWon = false;
        int decision = 0;
    };

    class TankArena
    {
    public:
        static constexpr int HORIZONTAL_CELLS = 11;
        static constexpr int VERTICAL_CELLS = 7;
        static constexpr int CELL_COUNT = HORIZONTAL_CELLS * VERTICAL_CELLS;
        static constexpr int MAX_SHELL_FEATURES = 8;
        static constexpr int OBSERVATION_SIZE = 12 + MAX_SHELL_FEATURES * 7 + CELL_COUNT * 4;

        explicit TankArena(ArenaConfig config = {});

        std::vector<float> reset(uint32_t seed);
        StepResult step(const TankAction& action);
        [[nodiscard]] std::vector<float> observation() const;
        [[nodiscard]] bool terminated() const;
        [[nodiscard]] bool truncated() const;
        [[nodiscard]] int decision() const;

    private:
        struct TankState
        {
            float x = 0.0F;
            float y = 0.0F;
            float angle = 0.0F;
            int ammo = 5;
        };

        struct ShellState
        {
            float x = 0.0F;
            float y = 0.0F;
            float angle = 0.0F;
            int owner = 0;
            int ttl = 180;
            int age = 0;
        };

        struct Wall
        {
            float x1 = 0.0F;
            float y1 = 0.0F;
            float x2 = 0.0F;
            float y2 = 0.0F;
            bool horizontal = false;
        };

        using WallMask = std::array<std::array<bool, 4>, CELL_COUNT>;

        void generateMaze();
        void buildWalls();
        void spawnTanks();
        void advanceTank(TankState& tank, const TankAction& action, bool permitFire, int owner);
        void advanceShells(StepResult& result);
        TankAction agentSmithAction() const;
        bool isTankPositionValid(float x, float y) const;
        const Wall* collidingWall(float x, float y, float radius) const;
        bool tankHit(const ShellState& shell, const TankState& tank) const;
        void spawnShell(const TankState& tank, int owner);
        static float normalizeAngle(float angle);
        static float angleTo(float fromX, float fromY, float toX, float toY);
        static float pointSegmentDistance(float px, float py, const Wall& wall);
        static int cellId(int x, int y);

        ArenaConfig config_;
        std::mt19937 rng_;
        std::array<std::array<bool, CELL_COUNT>, CELL_COUNT> connections_{};
        WallMask wallMask_{};
        std::vector<Wall> walls_;
        std::vector<ShellState> shells_;
        TankState player_;
        TankState opponent_;
        int decision_ = 0;
        bool terminated_ = false;
        bool truncated_ = false;
    };
}

#endif // TANK_TROUBLE_AI_TRAIN_TANK_ARENA_H
