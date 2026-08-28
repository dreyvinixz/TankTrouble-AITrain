#include "core/Math.h"
#include "core/Vec.h"
#include <cassert>
#include <cmath>
#include <iostream>
#include <vector>

namespace TankTrouble::Test
{
    void test_vec_math()
    {
        util::Vec v1(3.0, 4.0);
        assert(std::abs(v1.norm() - 5.0) < 1e-6);

        util::Vec v2(1.0, 2.0);
        util::Vec v3 = v1 + v2;
        assert(v3.x() == 4.0 && v3.y() == 6.0);

        util::Vec v4 = v1 - v2;
        assert(v4.x() == 2.0 && v4.y() == 2.0);

        double dot = v1 * v2;
        assert(dot == 11.0);

        double cross = v1.cross(v2);
        assert(cross == 3.0 * 2.0 - 4.0 * 1.0); // 2.0

        std::cout << "  [PASS] test_vec_math\n";
    }

    void test_geometry_and_corners()
    {
        util::Vec pos(100.0, 100.0);
        double angle = 0.0;
        int width = 20;
        int height = 28;

        std::array<util::Vec, 4> corners = util::getCornerVec(pos, angle, width, height);
        assert(corners.size() == 4);

        // Center between opposite corners should match original position
        double cx = (corners[0].x() + corners[3].x()) / 2.0;
        double cy = (corners[0].y() + corners[3].y()) / 2.0;
        assert(std::abs(cx - pos.x()) < 1e-4);
        assert(std::abs(cy - pos.y()) < 1e-4);

        std::cout << "  [PASS] test_geometry_and_corners\n";
    }

    void test_deterministic_rng()
    {
        util::setRandomSeed(12345);
        std::vector<int> seq1;
        for (int i = 0; i < 20; ++i)
        {
            seq1.push_back(util::getRandomNumber(0, 100));
        }

        util::setRandomSeed(12345);
        std::vector<int> seq2;
        for (int i = 0; i < 20; ++i)
        {
            seq2.push_back(util::getRandomNumber(0, 100));
        }

        assert(seq1 == seq2);
        std::cout << "  [PASS] test_deterministic_rng\n";
    }

    void test_collision_detection()
    {
        // Test non-overlapping rectangles
        bool col1 = util::checkRectRectCollision(0.0, util::Vec(0, 0), 20, 20,
                                                 0.0, util::Vec(100, 100), 20, 20);
        assert(!col1);

        // Test overlapping rectangles
        bool col2 = util::checkRectRectCollision(0.0, util::Vec(50, 50), 20, 20,
                                                 0.0, util::Vec(55, 55), 20, 20);
        assert(col2);

        std::cout << "  [PASS] test_collision_detection\n";
    }

    void run_all_math_tests()
    {
        std::cout << "[RUN] Math & Core Tests\n";
        test_vec_math();
        test_geometry_and_corners();
        test_deterministic_rng();
        test_collision_detection();
    }
}
