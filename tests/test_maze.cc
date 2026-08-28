#include "game/Maze.h"
#include "game/GameConfig.h"
#include <cassert>
#include <iostream>
#include <vector>

namespace TankTrouble::Test
{
    void test_maze_generation_bounds()
    {
        Maze maze;
        maze.generate();
        auto blocks = maze.getBlockPositions();

        assert(!blocks.empty());
        assert(blocks.size() <= MAX_BLOCKS_NUM);

        for (const auto& b : blocks)
        {
            const util::Vec& start = b.first;
            const util::Vec& end = b.second;

            // Coordinates must lie within game bounds
            assert(start.x() >= 0 && start.x() <= GAME_VIEW_WIDTH);
            assert(start.y() >= 0 && start.y() <= GAME_VIEW_HEIGHT);
            assert(end.x() >= 0 && end.x() <= GAME_VIEW_WIDTH);
            assert(end.y() >= 0 && end.y() <= GAME_VIEW_HEIGHT);

            // Block is either horizontal or vertical
            assert(start.x() == end.x() || start.y() == end.y());
        }

        std::cout << "  [PASS] test_maze_generation_bounds (generated " << blocks.size() << " blocks)\n";
    }

    void test_maze_multi_instance_isolation()
    {
        // Generate two mazes sequentially - ensures local visited state has no bleed-over
        Maze m1;
        m1.generate();
        auto b1 = m1.getBlockPositions();

        Maze m2;
        m2.generate();
        auto b2 = m2.getBlockPositions();

        assert(!b1.empty());
        assert(!b2.empty());
        std::cout << "  [PASS] test_maze_multi_instance_isolation\n";
    }

    void run_all_maze_tests()
    {
        std::cout << "[RUN] Maze Generation Tests\n";
        test_maze_generation_bounds();
        test_maze_multi_instance_isolation();
    }
}
