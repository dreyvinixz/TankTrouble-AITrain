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
        globalTick_ = 0;
        opponentNextFireTick_ = 0;
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
            // The baseline has its own tick scheduler and fire cooldown, so it
            // may legitimately fire on any simulation tick.
            advanceTank(opponent_, opponentAction, true, 1);
            result.reward += config_.survivalRewardPerTick;
            advanceShells(result);
            ++globalTick_;
        }

        ++decision_;
        if(!terminated_ && decision_ >= config_.maxDecisions)
        {
            truncated_ = true;
            result.reward += config_.timeoutReward;
        }

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
        bool playerHit = false;
        bool opponentHit = false;

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

            bool hit = false;
            if(shell.age > 2)
            {
                const bool hitP = tankHit(shell, player_);
                const bool hitO = tankHit(shell, opponent_);
                if(hitP || hitO)
                {
                    playerHit |= hitP;
                    opponentHit |= hitO;
                    hit = true;
                }
            }

            if(!hit)
            {
                if(shell.ttl > 0)
                    active.push_back(shell);
                else if(shell.owner == 0)
                    ++player_.ammo;
                else
                    ++opponent_.ammo;
            }
            else
            {
                if(shell.owner == 0)
                    ++player_.ammo;
                else
                    ++opponent_.ammo;
            }
        }
        shells_ = std::move(active);

        if(playerHit || opponentHit)
        {
            terminated_ = true;
            if(playerHit && opponentHit)
            {
                result.reward += config_.drawReward;
                result.playerWon = false;
            }
            else if(playerHit)
            {
                result.reward += config_.lossReward;
                result.playerWon = false;
            }
            else
            {
                result.reward += config_.winReward;
                result.playerWon = true;
            }
        }
    }

    TankAction TankArena::agentSmithAction()
    {
        // The legacy controller gives dodge strategies priority over attack
        // and contact strategies. Keep the same ordering in the deterministic
        // headless arena while using its compact state representation.
        for(const ShellState& shell: shells_)
            if(shell.owner == 0 && shellThreatensOpponent(shell))
                return dodgeAction();

        TankAction action = contactAction();
        const float dx = player_.x - opponent_.x;
        const float dy = player_.y - opponent_.y;
        const float distance = std::sqrt(dx * dx + dy * dy);

        // Agent Smith attacks when target is within physical bullet reach (~170px)
        // and there is an unobstructed direct line of sight.
        constexpr float kSmithFireRange = 170.0F;
        constexpr int kSmithFireCooldown = 30; // ~10 decisions at ticksPerAction=3

        if(globalTick_ >= opponentNextFireTick_
            && opponent_.ammo > 0 && distance <= kSmithFireRange && hasDirectShot())
        {
            const float desired = angleTo(opponent_.x, opponent_.y, player_.x, player_.y);
            float delta = desired - opponent_.angle;
            if(delta > 180.0F) delta -= 360.0F;
            if(delta < -180.0F) delta += 360.0F;
            if(std::abs(delta) < 4.0F)
            {
                action.fire = 1;
                opponentNextFireTick_ = globalTick_ + kSmithFireCooldown;
            }
        }
        return action;
    }

    TankAction TankArena::dodgeAction() const
    {
        TankAction action;
        const ShellState* threat = nullptr;
        for(const ShellState& shell: shells_)
            if(shell.owner == 0 && shellThreatensOpponent(shell))
            {
                threat = &shell;
                break;
            }
        if(threat == nullptr)
            return action;

        const float radians = threat->angle * kPi / 180.0F;
        const float directionX = std::cos(radians);
        const float directionY = -std::sin(radians);
        const float relativeX = opponent_.x - threat->x;
        const float relativeY = opponent_.y - threat->y;
        const float cross = directionX * relativeY - directionY * relativeX;
        // Turn away from the trajectory and move simultaneously, matching the
        // combined rotation/movement dodge commands in DodgeStrategy.
        action.rotation = cross >= 0.0F ? 1 : 2;
        action.movement = 1;
        return action;
    }

    TankAction TankArena::contactAction() const
    {
        TankAction action;
        float targetX = player_.x;
        float targetY = player_.y;
        if(!hasDirectShot())
        {
            const int nextCell = nextRouteCell();
            if(nextCell >= 0)
            {
                targetX = (nextCell % HORIZONTAL_CELLS + 0.5F) * kCellSize;
                targetY = (nextCell / HORIZONTAL_CELLS + 0.5F) * kCellSize;
            }
        }
        const float desired = angleTo(opponent_.x, opponent_.y, targetX, targetY);
        float delta = desired - opponent_.angle;
        if(delta > 180.0F) delta -= 360.0F;
        if(delta < -180.0F) delta += 360.0F;
        if(std::abs(delta) >= 12.0F)
            action.rotation = delta > 0.0F ? 2 : 1;
        if(std::abs(delta) < 45.0F)
            action.movement = 1;
        return action;
    }

    bool TankArena::shellThreatensOpponent(const ShellState& shell) const
    {
        constexpr float threatenedRange = 150.0F;
        const float dx = opponent_.x - shell.x;
        const float dy = opponent_.y - shell.y;
        if(dx * dx + dy * dy > threatenedRange * threatenedRange)
            return false;
        const float radians = shell.angle * kPi / 180.0F;
        const float directionX = std::cos(radians);
        const float directionY = -std::sin(radians);
        const float along = directionX * dx + directionY * dy;
        if(along < 0.0F || along > 75.0F)
            return false;
        const float lateral = std::abs(directionX * dy - directionY * dx);
        return lateral <= kTankRadius + kShellRadius + 3.0F;
    }

    bool TankArena::hasDirectShot() const
    {
        const float dx = player_.x - opponent_.x;
        const float dy = player_.y - opponent_.y;
        const auto crossesWall = [this, dx, dy](const Wall& wall)
        {
            if(wall.horizontal)
            {
                if(std::abs(dy) < std::numeric_limits<float>::epsilon())
                    return false;
                const float t = (wall.y1 - opponent_.y) / dy;
                if(t <= 0.0F || t >= 1.0F)
                    return false;
                const float x = opponent_.x + t * dx;
                return x > std::min(wall.x1, wall.x2) && x < std::max(wall.x1, wall.x2);
            }
            if(std::abs(dx) < std::numeric_limits<float>::epsilon())
                return false;
            const float t = (wall.x1 - opponent_.x) / dx;
            if(t <= 0.0F || t >= 1.0F)
                return false;
            const float y = opponent_.y + t * dy;
            return y > std::min(wall.y1, wall.y2) && y < std::max(wall.y1, wall.y2);
        };
        return std::none_of(walls_.begin(), walls_.end(), crossesWall);
    }

    int TankArena::nextRouteCell() const
    {
        const auto tankCell = [](const TankState& tank)
        {
            const int x = std::clamp(static_cast<int>(tank.x / kCellSize), 0, HORIZONTAL_CELLS - 1);
            const int y = std::clamp(static_cast<int>(tank.y / kCellSize), 0, VERTICAL_CELLS - 1);
            return cellId(x, y);
        };
        const int start = tankCell(opponent_);
        const int target = tankCell(player_);
        if(start == target)
            return -1;

        std::array<int, CELL_COUNT> previous{};
        previous.fill(-1);
        std::vector<int> queue = {start};
        previous[start] = start;
        for(size_t index = 0; index < queue.size() && previous[target] == -1; ++index)
        {
            const int current = queue[index];
            for(int next = 0; next < CELL_COUNT; ++next)
                if(connections_[current][next] && previous[next] == -1)
                {
                    previous[next] = current;
                    queue.push_back(next);
                }
        }
        if(previous[target] == -1)
            return -1;
        int next = target;
        while(previous[next] != start)
            next = previous[next];
        return next;
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

        const auto lidar = wallLidar(player_.x, player_.y, player_.angle);
        value.insert(value.end(), lidar.begin(), lidar.end());
        return value;
    }

    float TankArena::raycastWall(float originX, float originY, float rayAngle, float maxDistance) const
    {
        const float radians = rayAngle * kPi / 180.0F;
        const float dx = std::cos(radians);
        const float dy = -std::sin(radians);

        float minDistance = maxDistance;

        for(const auto& wall: walls_)
        {
            if(wall.horizontal)
            {
                if(std::abs(dy) < 1e-6F)
                    continue;
                const float t = (wall.y1 - originY) / dy;
                if(t > 0.0F && t < minDistance)
                {
                    const float hitX = originX + t * dx;
                    const float minX = std::min(wall.x1, wall.x2);
                    const float maxX = std::max(wall.x1, wall.x2);
                    if(hitX >= minX && hitX <= maxX)
                    {
                        minDistance = t;
                    }
                }
            }
            else
            {
                if(std::abs(dx) < 1e-6F)
                    continue;
                const float t = (wall.x1 - originX) / dx;
                if(t > 0.0F && t < minDistance)
                {
                    const float hitY = originY + t * dy;
                    const float minY = std::min(wall.y1, wall.y2);
                    const float maxY = std::max(wall.y1, wall.y2);
                    if(hitY >= minY && hitY <= maxY)
                    {
                        minDistance = t;
                    }
                }
            }
        }
        return minDistance;
    }

    std::array<float, TankArena::LIDAR_RAYS> TankArena::wallLidar(float x, float y, float angle) const
    {
        std::array<float, LIDAR_RAYS> lidar{};
        constexpr std::array<float, LIDAR_RAYS> kRayAngleOffsets = {
            0.0F, 45.0F, 90.0F, 135.0F, 180.0F, 225.0F, 270.0F, 315.0F
        };

        for(size_t i = 0; i < LIDAR_RAYS; ++i)
        {
            const float rayAngle = normalizeAngle(angle + kRayAngleOffsets[i]);
            const float dist = raycastWall(x, y, rayAngle, LIDAR_MAX_DISTANCE);
            lidar[i] = std::clamp(dist / LIDAR_MAX_DISTANCE, 0.0F, 1.0F);
        }
        return lidar;
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
