#include "ai/baselines/agent_smith/AStar.h"
#include "game/Block.h"
#include <cassert>
#include <iostream>

namespace TankTrouble::Test
{
    void test_astar_open_grid()
    {
        AStar astar;
        AStar::BlockList emptyBlocks;
        astar.init(&emptyBlocks);

        // Find route from (0,0) to (5,5)
        auto route = astar.findRoute(0, 0, 5, 5);
        assert(!route.empty());
        assert(route.front() == std::make_pair(0, 0));
        assert(route.back() == std::make_pair(5, 5));

        // Diagonal distance on open grid should take roughly 6 steps (0,0)->...->(5,5)
        assert(route.size() == 6);

        std::cout << "  [PASS] test_astar_open_grid (path length: " << route.size() << ")\n";
    }

    void test_astar_obstacle_detour()
    {
        AStar astar;
        AStar::BlockList blocks;

        // Place a horizontal wall blocking (2, 2)
        // Block between (2 * 60, 2 * 60) and (3 * 60, 2 * 60)
        Block b1(11, util::Vec(120.0, 120.0), util::Vec(180.0, 120.0));
        blocks[11] = b1;

        astar.init(&blocks);
        auto route = astar.findRoute(2, 1, 2, 3);
        assert(!route.empty());
        assert(route.front() == std::make_pair(2, 1));
        assert(route.back() == std::make_pair(2, 3));

        std::cout << "  [PASS] test_astar_obstacle_detour (detour path length: " << route.size() << ")\n";
    }

    void test_astar_discards_stale_queue_entries()
    {
        AStar astar;
        AStar::BlockList blocks;
        // These walls force competing partial routes to the same cells. The
        // optimized implementation keeps the stale heap entries and discards
        // them lazily when popped instead of rebuilding the priority queue.
        blocks.emplace(21, Block(21, util::Vec(120.0, 0.0), util::Vec(120.0, 300.0)));
        blocks.emplace(22, Block(22, util::Vec(300.0, 120.0), util::Vec(300.0, 420.0)));
        blocks.emplace(23, Block(23, util::Vec(60.0, 180.0), util::Vec(420.0, 180.0)));

        astar.init(&blocks);
        const auto route = astar.findRoute(0, 0, 10, 6);
        assert(!route.empty());
        assert(route.front() == std::make_pair(0, 0));
        assert(route.back() == std::make_pair(10, 6));
        assert(astar.staleEntriesDiscarded() > 0);

        std::cout << "  [PASS] test_astar_discards_stale_queue_entries (discarded: "
                  << astar.staleEntriesDiscarded() << ")\n";
    }

    void run_all_astar_tests()
    {
        std::cout << "[RUN] A* Pathfinding Tests\n";
        test_astar_open_grid();
        test_astar_obstacle_detour();
        test_astar_discards_stale_queue_entries();
    }
}
