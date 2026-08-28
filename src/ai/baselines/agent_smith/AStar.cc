#include "AStar.h"
#include "Block.h"
#include <cassert>
#include <cmath>

namespace TankTrouble
{
    const static int dx[] = {0, -1, -1, -1, 0, 1, 1, 1};
    const static int dy[] = {-1, -1, 0, 1, 1, 1, 0, -1};

    void AStar::init(TankTrouble::AStar::BlockList *blocks)
    {
        map = std::vector(MAX_A_STAR_NODE_ID, std::vector<int>(MAX_A_STAR_NODE_ID));
        for(const auto& entry: *blocks)
        {
            const Block& block = entry.second;
            util::Vec blockStart = block.start();
            util::Vec blockEnd = block.end();
            if(block.isHorizon())
            {
                int topLeftGridId = getGridId(MAP_REAL_X_TO_A_STAR_X(blockStart.x() - A_STAR_GRID_SIZE / 2),
                                              MAP_REAL_Y_TO_A_STAR_Y(blockStart.y() - A_STAR_GRID_SIZE / 2));
                int bottomLeftGridId = getGridId(MAP_REAL_X_TO_A_STAR_X(blockStart.x() - A_STAR_GRID_SIZE / 2),
                                                 MAP_REAL_Y_TO_A_STAR_Y(blockStart.y() + A_STAR_GRID_SIZE / 2));
                int topRightGridId = getGridId(MAP_REAL_X_TO_A_STAR_X(blockEnd.x() + A_STAR_GRID_SIZE / 2),
                                               MAP_REAL_Y_TO_A_STAR_Y(blockEnd.y() - A_STAR_GRID_SIZE / 2));
                int bottomRightGridId = getGridId(MAP_REAL_X_TO_A_STAR_X(blockEnd.x() + A_STAR_GRID_SIZE / 2),
                                                  MAP_REAL_Y_TO_A_STAR_Y(blockEnd.y() + A_STAR_GRID_SIZE / 2));
                double y1 = blockStart.y() - A_STAR_GRID_SIZE / 2;
                double y2 = blockStart.y() + A_STAR_GRID_SIZE / 2;
                double x1, x2;
                for(int i = 0; i < A_STAR_GRID_PER_GRID; i++)
                {
                    x1 = block.start().x() + i * A_STAR_GRID_SIZE + A_STAR_GRID_SIZE / 2;
                    int id1 = getGridId(MAP_REAL_X_TO_A_STAR_X(x1), MAP_REAL_Y_TO_A_STAR_Y(y1));
                    if(i == 0 && bottomLeftGridId < MAX_A_STAR_NODE_ID)
                        map[id1][bottomLeftGridId] = map[bottomLeftGridId][id1] = UNREACHABLE;
                    if(i == A_STAR_GRID_PER_GRID - 1 && bottomRightGridId < MAX_A_STAR_NODE_ID)
                        map[id1][bottomRightGridId] = map[bottomRightGridId][id1] = UNREACHABLE;
                    for(int j = 0; j < A_STAR_GRID_PER_GRID; j++)
                    {
                        x2 = block.start().x() + j * A_STAR_GRID_SIZE + A_STAR_GRID_SIZE / 2;
                        int id2 = getGridId(MAP_REAL_X_TO_A_STAR_X(x2), MAP_REAL_Y_TO_A_STAR_Y(y2));
                        map[id1][id2] = map[id2][id1] = UNREACHABLE;
                        if(j == 0 && topLeftGridId < MAX_A_STAR_NODE_ID)
                            map[id2][topLeftGridId] = map[topLeftGridId][id2] = UNREACHABLE;
                        if(j == A_STAR_GRID_PER_GRID - 1 && topRightGridId < MAX_A_STAR_NODE_ID)
                            map[id2][topRightGridId] = map[topRightGridId][id2] = UNREACHABLE;
                    }
                }
             }
            else
            {
                int topLeftGridId = getGridId(MAP_REAL_X_TO_A_STAR_X(blockStart.x() - A_STAR_GRID_SIZE / 2),
                                              MAP_REAL_Y_TO_A_STAR_Y(blockStart.y() - A_STAR_GRID_SIZE / 2));
                int bottomLeftGridId = getGridId(MAP_REAL_X_TO_A_STAR_X(blockEnd.x() - A_STAR_GRID_SIZE / 2),
                                                 MAP_REAL_Y_TO_A_STAR_Y(blockEnd.y() + A_STAR_GRID_SIZE / 2));
                int topRightGridId = getGridId(MAP_REAL_X_TO_A_STAR_X(blockStart.x() + A_STAR_GRID_SIZE / 2),
                                               MAP_REAL_Y_TO_A_STAR_Y(blockStart.y() - A_STAR_GRID_SIZE / 2));
                int bottomRightGridId = getGridId(MAP_REAL_X_TO_A_STAR_X(blockEnd.x() + A_STAR_GRID_SIZE / 2),
                                                  MAP_REAL_Y_TO_A_STAR_Y(blockEnd.y() + A_STAR_GRID_SIZE / 2));
                double x1 = blockStart.x() - A_STAR_GRID_SIZE / 2;
                double x2 = blockStart.x() + A_STAR_GRID_SIZE / 2;
                double y1, y2;
                for(int i = 0; i < A_STAR_GRID_PER_GRID; i++)
                {
                    y1 = block.start().y() + i * A_STAR_GRID_SIZE + A_STAR_GRID_SIZE / 2;
                    int id1 = getGridId(MAP_REAL_X_TO_A_STAR_X(x1), MAP_REAL_Y_TO_A_STAR_Y(y1));
                    if(i == 0 && topRightGridId < MAX_A_STAR_NODE_ID)
                        map[id1][topRightGridId] = map[topRightGridId][id1] = UNREACHABLE;
                    if(i == A_STAR_GRID_PER_GRID - 1 && bottomRightGridId < MAX_A_STAR_NODE_ID)
                        map[id1][bottomRightGridId] = map[bottomRightGridId][id1] = UNREACHABLE;
                    for(int j = 0; j < A_STAR_GRID_PER_GRID; j++)
                    {
                        y2 = block.start().y() + j * A_STAR_GRID_SIZE + A_STAR_GRID_SIZE / 2;
                        int id2 = getGridId(MAP_REAL_X_TO_A_STAR_X(x2), MAP_REAL_Y_TO_A_STAR_Y(y2));
                        map[id1][id2] = map[id2][id1] = UNREACHABLE;
                        if(j == 0 && topLeftGridId < MAX_A_STAR_NODE_ID)
                            map[id2][topLeftGridId] = map[topLeftGridId][id2] = UNREACHABLE;
                        if(j == A_STAR_GRID_PER_GRID - 1 && bottomLeftGridId < MAX_A_STAR_NODE_ID)
                            map[id2][bottomLeftGridId] = map[bottomLeftGridId][id2] = UNREACHABLE;
                    }
                }
            }
        }
    }

    AStar::AStarResult AStar::findRoute(int sx, int sy, int ex, int ey)
    {
        staleEntriesDiscarded_ = 0;
        AStarResult res;
        int id = getRoute(sx, sy, ex, ey);
        while(id != -1)
        {
            res.push_front(std::make_pair(nodes[id]->x, nodes[id]->y));
            id = nodes[id]->parentId;
        }
        EntryList().swap(entryList);
        openSet.clear();
        closedSet.clear();
        nodes.clear();
        return res;
    }

    size_t AStar::staleEntriesDiscarded() const {return staleEntriesDiscarded_;}

    int AStar::getGridId(int x, int y) {return y * static_cast<int>(HORIZON_A_STAR_GRID_NUMBER) + x;}

    int AStar::calcG(AStarNode* parent, AStarNode* cur)
    {
        assert(parent != nullptr && cur != nullptr);
        int curG = (cur->x == parent->x || cur->y == parent->y) ? HORIZON_VERTICAL_COST : DIAGONAL_COST;
        return parent->G + curG;
    }

    int AStar::calcH(AStarNode* cur, int ex, int ey)
    {
        assert(cur != nullptr);
        int dx = ex - cur->x;
        int dy = ey - cur->y;
        return static_cast<int>(std::sqrt(dx * dx + dy * dy));
    }

    std::vector<AStar::AStarNode> AStar::getReachable(int x, int y)
    {
        std::vector<AStarNode> reachable;
        for(int i = 0; i < 8; i++)
        {
            int nx = x + dx[i];
            int ny = y + dy[i];
            if(nx < 0 || nx >= HORIZON_A_STAR_GRID_NUMBER || ny < 0 || ny >= VERTICAL_A_STAR_GRID_NUMBER)
                continue;
            int currentId = getGridId(x, y);
            int nextId = getGridId(nx, ny);
            if(map[currentId][nextId] != REACHABLE || closedSet.find(nextId) != closedSet.end())
                continue;
            reachable.emplace_back(nx, ny);
        }
        return reachable;
    }

    void AStar::addToOpenList(std::unique_ptr<AStarNode>&& node)
    {
        entryList.push(std::make_pair(node->F, node->id));
        openSet.insert(node->id);
        nodes[node->id] = std::move(node);
    }

    int AStar::getRoute(int sx, int sy, int ex, int ey)
    {
        auto start = std::make_unique<AStarNode>(sx, sy);
        addToOpenList(std::move(start));
        int endId = getGridId(ex, ey);
        while(!entryList.empty())
        {
            Entry smallestF = entryList.top();
            entryList.pop();
            int curId = smallestF.second;
            if(closedSet.find(curId) != closedSet.end())
            {
                ++staleEntriesDiscarded_;
                continue;
            }
            AStarNode* cur = nodes[curId].get();
            if(smallestF.first > cur->F)
            {
                ++staleEntriesDiscarded_;
                continue;
            }
            openSet.erase(cur->id);
            closedSet.insert(cur->id);
            if(cur->id == endId)
                return endId;
            std::vector<AStarNode> reachable = getReachable(cur->x, cur->y);
            for(const AStarNode& n : reachable)
            {
                if(closedSet.find(n.id) != closedSet.end())
                    continue;
                if(openSet.find(n.id) == openSet.end())
                {
                    auto next = std::make_unique<AStarNode>(n.x, n.y);
                    next->parentId = cur->id;
                    next->G = calcG(cur, next.get());
                    next->H = calcH(next.get(), ex, ey);
                    next->F = next->G + next->H;
                    addToOpenList(std::move(next));
                }
                else
                {
                    AStarNode* next = nodes[n.id].get();
                    int testG = calcG(cur, next);
                    if(testG < next->G)
                    {
                        next->G = testG;
                        next->F = next->G + next->H;
                        next->parentId = cur->id;
                        entryList.push(std::make_pair(next->F, next->id));
                    }
                }
            }
        }
        return -1;
    }
}
