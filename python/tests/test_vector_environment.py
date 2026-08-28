"""Native bridge contract tests; run after build_native.sh."""

from __future__ import annotations

import unittest

import numpy as np

from tanktrain.environment import EnvironmentConfig, TankTrainVectorEnv


class VectorEnvironmentTest(unittest.TestCase):
    def test_seed_and_step_contract(self) -> None:
        config = EnvironmentConfig(num_envs=2, max_decisions=1)
        environment = TankTrainVectorEnv(config)
        first = environment.reset(31)
        second = environment.reset(31)
        np.testing.assert_array_equal(first, second)
        self.assertEqual(first.shape, (2, environment.observation_size))
        observation, reward, terminated, truncated = environment.step(np.array([[1, 2, 1], [0, 0, 0]]))
        self.assertEqual(observation.shape, first.shape)
        self.assertEqual(reward.shape, (2,))
        self.assertTrue(np.isfinite(reward).all())
        self.assertTrue((terminated | truncated).all())

    def test_timeout_and_v2_rewards(self) -> None:
        config = EnvironmentConfig(
            num_envs=1,
            max_decisions=1,
            survival_reward=0.0,
            timeout_reward=-0.20,
            win_reward=1.0,
            loss_reward=-1.0,
            draw_reward=0.0,
        )
        environment = TankTrainVectorEnv(config)
        environment.reset(999)
        _, reward, terminated, truncated = environment.step(np.array([[0, 0, 0]]))
        if truncated[0]:
            self.assertAlmostEqual(float(reward[0]), -0.20, places=5)
            self.assertFalse(terminated[0])


if __name__ == "__main__":
    unittest.main()
