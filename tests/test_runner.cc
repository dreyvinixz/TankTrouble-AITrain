#include <iostream>
#include <chrono>
#include "GameConfig.h"
#include "core/Vec.h"
#include "cairomm/context.h"
#include "app/ui/component/GameArea.h"

namespace TankTrouble
{
    void GameArea::drawRect(const Cairo::RefPtr<Cairo::Context>&, Color,
                           util::Vec, util::Vec, util::Vec, util::Vec) {}
}

namespace TankTrouble::Test
{
    void run_all_math_tests();
    void run_all_maze_tests();
    void run_all_astar_tests();
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  TankTrouble AI Train - Test Suite     \n";
    std::cout << "========================================\n\n";

    auto start = std::chrono::high_resolution_clock::now();

    TankTrouble::Test::run_all_math_tests();
    std::cout << "\n";
    TankTrouble::Test::run_all_maze_tests();
    std::cout << "\n";
    TankTrouble::Test::run_all_astar_tests();

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();

    std::cout << "\n========================================\n";
    std::cout << "  ALL TESTS PASSED (" << duration << " us) \n";
    std::cout << "========================================\n";

    return 0;
}
