#include "TankArena.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>

namespace TankTrouble::training
{
    namespace
    {
        constexpr float kCellSize = 60.0F;
        constexpr float kWidth = TankArena::HORIZONTAL_CELLS * kCellSize;
        constexpr float kHeight = TankArena::VERTICAL_CELLS * kCellSize;
        constexpr float kTankRadius = 14.0F;
        constexpr float kShellRadius = 2.5F;
        constexpr float kPi = 3.14159265358979323846F;
        constexpr std::array<int, 4> kDx = {0, 1, 0, -1};
        constexpr std::array<int, 4> kDy = {-1, 0, 1, 0};
        constexpr std::array<int, 4> kOpposite = {2, 3, 0, 1};
    }

    TankArena::TankArena(ArenaConfig config): config_(config), rng_(config.seed)
    {
        reset(config.seed);
    }

    std::vector<float> TankArena::reset(uint32_t seed)
    {
        rng_.seed(seed);
        decision_ = 0;
        terminated_ = false;
        truncated_ = false;
        shells_.clear();
        generateMaze();
        buildWalls();
        spawnTanks();
        return observation();
    }

    StepResult TankArena::step(const TankAction& requestedAction)
    {
        StepResult result;
        if(terminated_ || truncated_)
        {
            result.observation = observation();
            result.terminated = terminated_;
            result.truncated = truncated_;
            result.decision = decision_;
            return result;
        }

        TankAction action = requestedAction;
        action.movement = std::min<uint8_t>(action.movement, 2);
        action.rotation = std::min<uint8_t>(action.rotation, 2);
        action.fire = std::min<uint8_t>(action.fire, 1);

        for(int tick = 0; tick < config_.ticksPerAction && !terminated_; ++tick)
        {
            advanceTank(player_, action, tick == 0, 0);
            const TankAction opponentAction = agentSmithAction();
            advanceTank(opponent_, opponentAction, tick == 0, 1);
            result.reward += config_.survivalRewardPerTick;
            advanceShells(result);
        }

        ++decision_;
        if(!terminated_ && decision_ >= config_.maxDecisions)
            truncated_ = true;

        result.observation = observation();
        result.terminated = terminated_;
        result.truncated = truncated_;
        result.decision = decision_;
        return result;
    }

    bool TankArena::terminated() const {return terminated_;}
    bool TankArena::truncated() const {return truncated_;}
    int TankArena::decision() const {return decision_;}

    void TankArena::generateMaze()
    {
        for(auto& row: connections_)
            row.fill(false);

        std::array<bool, CELL_COUNT> visited{};
        std::vector<int> stack = {0};
        visited[0] = true;
        while(!stack.empty())
        {
            const int current = stack.back();
            const int x = current % HORIZONTAL_CELLS;
            const int y = current / HORIZONTAL_CELLS;
            std::array<int, 4> directions = {0, 1, 2, 3};
            std::shuffle(directions.begin(), directions.end(), rng_);
            bool advanced = false;
            for(const int direction: directions)
            {
                const int nx = x + kDx[direction];
                const int ny = y + kDy[direction];
                if(nx < 0 || nx >= HORIZONTAL_CELLS || ny < 0 || ny >= VERTICAL_CELLS)
                    continue;
                const int next = cellId(nx, ny);
                if(visited[next])
                    continue;
                connections_[current][next] = true;
                connections_[next][current] = true;
                visited[next] = true;
                stack.push_back(next);
                advanced = true;
                break;
            }
            if(!advanced)
                stack.pop_back();
        }
    }

    void TankArena::buildWalls()
    {
        walls_.clear();
        for(auto& mask: wallMask_)
            mask.fill(true);

        auto addWall = [this](float x1, float y1, float x2, float y2, bool horizontal)
        {
            walls_.push_back({x1, y1, x2, y2, horizontal});
        };

        addWall(0.0F, 0.0F, kWidth, 0.0F, true);
        addWall(0.0F, kHeight, kWidth, kHeight, true);
        addWall(0.0F, 0.0F, 0.0F, kHeight, false);
        addWall(kWidth, 0.0F, kWidth, kHeight, false);

        for(int y = 0; y < VERTICAL_CELLS; ++y)
            for(int x = 0; x < HORIZONTAL_CELLS; ++x)
            {
                const int current = cellId(x, y);
                for(int direction = 0; direction < 4; ++direction)
                {
                    const int nx = x + kDx[direction];
                    const int ny = y + kDy[direction];
                    if(nx < 0 || nx >= HORIZONTAL_CELLS || ny < 0 || ny >= VERTICAL_CELLS)
                        continue;
                    const int next = cellId(nx, ny);
                    const bool blocked = !connections_[current][next];
                    wallMask_[current][direction] = blocked;
                    if(blocked && direction < 2)
                    {
                        if(direction == 0)
                            addWall(x * kCellSize, y * kCellSize, (x + 1) * kCellSize, y * kCellSize, true);
                        else
                            addWall((x + 1) * kCellSize, y * kCellSize, (x + 1) * kCellSize, (y + 1) * kCellSize, false);
                    }
                }
            }
    }

    void TankArena::spawnTanks()
    {
        std::array<int, CELL_COUNT> cells{};
        std::iota(cells.begin(), cells.end(), 0);
        std::shuffle(cells.begin(), cells.end(), rng_);
        const auto spawn = [](int cell)
        {
            TankState tank;
            const int x = cell % HORIZONTAL_CELLS;
            const int y = cell / HORIZONTAL_CELLS;
            tank.x = (x + 0.5F) * kCellSize;
            tank.y = (y + 0.5F) * kCellSize;
            tank.angle = static_cast<float>((cell % 4) * 90);
            return tank;
        };
        player_ = spawn(cells[0]);
        opponent_ = spawn(cells[1]);
    }

    void TankArena::advanceTank(TankState& tank, const TankAction& action, bool permitFire, int owner)
    {
        if(action.rotation == 1) tank.angle = normalizeAngle(tank.angle - 3.0F);
        if(action.rotation == 2) tank.angle = normalizeAngle(tank.angle + 3.0F);
        if(action.movement != 0)
        {
            const float direction = action.movement == 1 ? tank.angle : tank.angle + 180.0F;
            const float radians = direction * kPi / 180.0F;
            const float nextX = tank.x + std::cos(radians);
            const float nextY = tank.y - std::sin(radians);
            if(isTankPositionValid(nextX, nextY))
            {
                tank.x = nextX;
                tank.y = nextY;
            }
        }
        if(permitFire && action.fire == 1 && tank.ammo > 0)
            spawnShell(tank, owner);
    }

    void TankArena::advanceShells(StepResult& result)
    {
        std::vector<ShellState> active;
        active.reserve(shells_.size());
        for(auto shell: shells_)
        {
            const float radians = shell.angle * kPi / 180.0F;
            const float nextX = shell.x + std::cos(radians);
            const float nextY = shell.y - std::sin(radians);
            if(const Wall* wall = collidingWall(nextX, nextY, kShellRadius))
            {
                shell.angle = wall->horizontal ? normalizeAngle(360.0F - shell.angle)
                                               : normalizeAngle(180.0F - shell.angle);
            }
            else
            {
                shell.x = nextX;
                shell.y = nextY;
            }
            ++shell.age;
            --shell.ttl;

            if(shell.age > 2 && tankHit(shell, shell.owner == 0 ? opponent_ : player_))
            {
                const bool playerHit = shell.owner == 0;
                result.reward += playerHit ? config_.hitOpponentReward + config_.winReward
                                           : config_.hitByOpponentReward + config_.lossReward;
                result.playerWon = playerHit;
                terminated_ = true;
                break;
            }
            if(shell.ttl > 0)
                active.push_back(shell);
            else if(shell.owner == 0)
                ++player_.ammo;
            else
                ++opponent_.ammo;
        }
        shells_ = std::move(active);
    }

    TankAction TankArena::agentSmithAction() const
    {
        TankAction action;
        const float desired = angleTo(opponent_.x, opponent_.y, player_.x, player_.y);
        float delta = desired - opponent_.angle;
        if(delta > 180.0F) delta -= 360.0F;
        if(delta < -180.0F) delta += 360.0F;
        if(std::abs(delta) > 6.0F)
            action.rotation = delta > 0.0F ? 2 : 1;
        const float dx = player_.x - opponent_.x;
        const float dy = player_.y - opponent_.y;
        const float distance = std::sqrt(dx * dx + dy * dy);
        if(distance > 90.0F)
            action.movement = 1;
        if(std::abs(delta) < 9.0F && distance < 320.0F && opponent_.ammo > 0)
            action.fire = 1;
        return action;
    }

    bool TankArena::isTankPositionValid(float x, float y) const
    {
        return x >= kTankRadius && x <= kWidth - kTankRadius && y >= kTankRadius && y <= kHeight - kTankRadius
            && collidingWall(x, y, kTankRadius) == nullptr;
    }

    const TankArena::Wall* TankArena::collidingWall(float x, float y, float radius) const
    {
        for(const auto& wall: walls_)
            if(pointSegmentDistance(x, y, wall) <= radius + 2.0F)
                return &wall;
        return nullptr;
    }

    bool TankArena::tankHit(const ShellState& shell, const TankState& tank) const
    {
        const float dx = shell.x - tank.x;
        const float dy = shell.y - tank.y;
        return dx * dx + dy * dy <= (kTankRadius + kShellRadius) * (kTankRadius + kShellRadius);
    }

    void TankArena::spawnShell(const TankState& tank, int owner)
    {
        const float radians = tank.angle * kPi / 180.0F;
        shells_.push_back({tank.x + 17.0F * std::cos(radians), tank.y - 17.0F * std::sin(radians), tank.angle, owner});
        if(owner == 0) --player_.ammo;
        else --opponent_.ammo;
    }

    std::vector<float> TankArena::observation() const
    {
        std::vector<float> value;
        value.reserve(OBSERVATION_SIZE);
        const auto appendTank = [&value](const TankState& tank)
        {
            const float radians = tank.angle * kPi / 180.0F;
            value.insert(value.end(), {tank.x / kWidth, tank.y / kHeight, std::sin(radians), std::cos(radians),
                                       static_cast<float>(tank.ammo) / 5.0F, 1.0F});
        };
        appendTank(player_);
        appendTank(opponent_);

        std::vector<ShellState> ordered = shells_;
        std::sort(ordered.begin(), ordered.end(), [this](const ShellState& left, const ShellState& right)
        {
            const float leftDx = left.x - player_.x;
            const float leftDy = left.y - player_.y;
            const float rightDx = right.x - player_.x;
            const float rightDy = right.y - player_.y;
            return leftDx * leftDx + leftDy * leftDy < rightDx * rightDx + rightDy * rightDy;
        });
        for(int i = 0; i < MAX_SHELL_FEATURES; ++i)
        {
            if(i >= static_cast<int>(ordered.size()))
            {
                value.insert(value.end(), 7, 0.0F);
                continue;
            }
            const auto& shell = ordered[i];
            const float radians = shell.angle * kPi / 180.0F;
            value.insert(value.end(), {(shell.x - player_.x) / kWidth, (shell.y - player_.y) / kHeight,
                                       std::sin(radians), std::cos(radians), shell.owner == 0 ? 1.0F : -1.0F,
                                       static_cast<float>(shell.ttl) / 180.0F, 1.0F});
        }
        for(const auto& mask: wallMask_)
            for(const bool blocked: mask)
                value.push_back(blocked ? 1.0F : 0.0F);
        return value;
    }

    float TankArena::normalizeAngle(float angle)
    {
        while(angle < 0.0F) angle += 360.0F;
        while(angle >= 360.0F) angle -= 360.0F;
        return angle;
    }

    float TankArena::angleTo(float fromX, float fromY, float toX, float toY)
    {
        return normalizeAngle(std::atan2(-(toY - fromY), toX - fromX) * 180.0F / kPi);
    }

    float TankArena::pointSegmentDistance(float px, float py, const Wall& wall)
    {
        const float dx = wall.x2 - wall.x1;
        const float dy = wall.y2 - wall.y1;
        const float lengthSquared = dx * dx + dy * dy;
        const float rawT = ((px - wall.x1) * dx + (py - wall.y1) * dy) / lengthSquared;
        const float t = std::max(0.0F, std::min(1.0F, rawT));
        const float sx = wall.x1 + t * dx;
        const float sy = wall.y1 + t * dy;
        const float diffX = px - sx;
        const float diffY = py - sy;
        return std::sqrt(diffX * diffX + diffY * diffY);
    }

    int TankArena::cellId(int x, int y) {return y * HORIZONTAL_CELLS + x;}
}
