cmake_minimum_required(VERSION 3.8)
project(TankTroubleAITrain VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_BUILD_TYPE Debug)

option(TANKTRAIN_BUILD_PYTHON_BINDINGS "Build the pybind11 training environment module" OFF)
option(TANKTRAIN_BUILD_TESTS "Build deterministic training-environment and core tests" ON)

set(TANK_CORE_SRC
        src/core/Vec.cc
        src/core/Math.cc
        src/core/Id.cc)

set(TANK_GAME_SRC
        src/game/Tank.cc
        src/game/Shell.cc
        src/game/Block.cc
        src/game/Object.cc
        src/game/Maze.cc
        src/game/Controller.cc
        src/game/controllers/LocalController.cc
        src/game/controllers/OnlineController.cc
        src/game/network/Codec.cc
        src/game/events/ControlEvent.cc)

set(TANK_AI_SRC
        src/ai/baselines/agent_smith/AgentSmith.cc
        src/ai/baselines/agent_smith/DodgeStrategy.cc
        src/ai/baselines/agent_smith/AStar.cc
        src/ai/baselines/agent_smith/ContactStrategy.cc
        src/ai/baselines/agent_smith/AttackStrategy.cc)

set(TANK_APP_SRC
        src/app/main.cc
        src/app/Window.cc
        src/app/ui/EntryView.cc
        src/app/ui/LoginView.cc
        src/app/ui/GameLobby.cc
        src/app/ui/GameView.cc
        src/app/ui/component/GameArea.cc
        src/app/ui/component/RoomItem.cc
        src/app/ui/component/PlayerInfoItem.cc)

set(TANK_TRAIN_SRC
        ${TANK_APP_SRC}
        ${TANK_GAME_SRC}
        ${TANK_CORE_SRC}
        ${TANK_AI_SRC})

find_package(PkgConfig)
pkg_check_modules(GTKMM gtkmm-3.0)

set(EV_INCLUDE_DIRS ${CMAKE_CURRENT_SOURCE_DIR}/third_party/ev/ev)
set(EV_LIBRARY_DIRS ${CMAKE_BINARY_DIR}/third_party/ev/ev/reactor ${CMAKE_BINARY_DIR}/third_party/ev/ev/net)
add_subdirectory(third_party/ev)

include_directories(${GTKMM_INCLUDE_DIRS} ${EV_INCLUDE_DIRS} src src/app src/game src/core src/ai/baselines/agent_smith)
link_directories(${GTKMM_LIBRARY_DIRS} ${EV_LIBRARY_DIRS})
link_libraries(${GTKMM_LIBRARIES} reactor net pthread)

file(COPY ${CMAKE_SOURCE_DIR}/res/entry.jpg DESTINATION ${CMAKE_BINARY_DIR})
add_executable(TankTroubleAITrain ${TANK_TRAIN_SRC})

add_library(tanktrain_arena STATIC
        src/training/environment/TankArena.cc
        src/core/Vec.cc
        src/core/Math.cc
        src/core/Id.cc
        src/game/Maze.cc)
target_include_directories(tanktrain_arena PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/src
        ${CMAKE_CURRENT_SOURCE_DIR}/src/core
        ${CMAKE_CURRENT_SOURCE_DIR}/src/game
        ${CMAKE_CURRENT_SOURCE_DIR}/src/training)

if(TANKTRAIN_BUILD_TESTS)
    enable_testing()

    add_executable(TankTrainEnvironmentTests tests/training/test_tank_arena.cc)
    target_link_libraries(TankTrainEnvironmentTests PRIVATE tanktrain_arena)
    add_test(NAME tanktrain_environment COMMAND TankTrainEnvironmentTests)

    add_executable(TankTrainCoreTests
            tests/test_runner.cc
            tests/test_math.cc
            tests/test_maze.cc
            tests/test_astar.cc
            src/ai/baselines/agent_smith/AStar.cc
            src/game/Block.cc
            src/game/Shell.cc
            src/game/Object.cc)
    target_include_directories(TankTrainCoreTests PRIVATE
            ${CMAKE_CURRENT_SOURCE_DIR}/tests/stubs
            ${CMAKE_CURRENT_SOURCE_DIR}/src
            ${CMAKE_CURRENT_SOURCE_DIR}/src/game
            ${CMAKE_CURRENT_SOURCE_DIR}/src/core
            ${CMAKE_CURRENT_SOURCE_DIR}/src/ai/baselines/agent_smith)
    target_link_libraries(TankTrainCoreTests PRIVATE tanktrain_arena)
    add_test(NAME tanktrain_core_suite COMMAND TankTrainCoreTests)
endif()

if(TANKTRAIN_BUILD_PYTHON_BINDINGS)
    find_package(pybind11 CONFIG REQUIRED)
    pybind11_add_module(tanktrain_env src/training/bindings/pybind_module.cc)
    target_link_libraries(tanktrain_env PRIVATE tanktrain_arena)
    target_include_directories(tanktrain_env PRIVATE
            ${CMAKE_CURRENT_SOURCE_DIR}/src
            ${CMAKE_CURRENT_SOURCE_DIR}/src/training)
    set_target_properties(tanktrain_env PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
endif()
