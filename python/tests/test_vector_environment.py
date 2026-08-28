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


if __name__ == "__main__":
    unittest.main()
