# Code reference: https://github.com/Lizhi-sjtu/DRL-code-pytorch/tree/main/3.Rainbow_DQN

import sys

sys.path.append(".")
import os
from torch.utils.tensorboard import SummaryWriter
from RL.util.replay_buffer_DQN import Multi_step_ReplayBuffer_multi_info
import random
from tqdm import tqdm
import argparse
from model.net import *
import numpy as np
import torch
from torch import nn
import yaml
import pandas as pd
from env.low_level_env import Testing_env, Training_Env
from env.high_level_env import high_level_testing_env

import copy
from RL.util.graph import get_test_contrast_curve_high_level, get_test_contrast_curve
from RL.util.episode_selector import start_selector, get_transformation_exp
import re

os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["F_ENABLE_ONEDNN_OPTS"] = "0"

parser = argparse.ArgumentParser()

# trading setting
parser.add_argument(
    "--transcation_cost",
    type=float,
    default=0.00015,
    help="the transcation cost of not holding the same action as before",
)
parser.add_argument(
    "--max_holding_number",
    type=float,
    default=0.01,
    help="the transcation cost of not holding the same action as before",
)
parser.add_argument(
    "--action_dim",
    type=int,
    default=5,
    help="the number of action we have in the training and testing env",
)
parser.add_argument(
    "--back_time_length", type=int, default=1, help="the length of the holding period"
)
# model list setting
parser.add_argument(
    "--dataset_name",
    type=str,
    default="BTCUSDT",
    help="the transcation cost of not holding the same action as before",
)
# data


parser.add_argument(
    "--test_data_path",
    type=str,
    default="data/BTCUSDT/test.feather",
    help="the path of test df",
)
parser.add_argument(
    "--valid_data_path",
    type=str,
    default="data/BTCUSDT/valid.feather",
    help="the path of valid df",
)
parser.add_argument(
    "--action",
    type=int,
    default=0,
    help="single agent index",
)
parser.add_argument(
    "--save_path",
    type=str,
    default="result_risk/BTCUSDT/high_level_single_agent",
    help="save path",
)


def sort_list(lst: list):
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split("([0-9]+)", key)]
    lst.sort(key=alphanum_key)


class trader(object):
    def __init__(self, args) -> None:
        if torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        # trading setting
        assert args.dataset_name in ["BTCUSDT", "ETHUSDT", "GALAUSDT", "BTCTUSD"]
        if args.dataset_name == "BTCUSDT":
            model_path_list_dict = {
                0: [
                    "result_risk/BTCUSDT/potential_model/initial_action_0/model_0.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_0/model_1.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_0/model_2.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_0/model_3.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_0/model_4.pth",
                ],
                1: [
                    "result_risk/BTCUSDT/potential_model/initial_action_1/model_0.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_1/model_1.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_1/model_2.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_1/model_3.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_1/model_4.pth",
                ],
                2: [
                    "result_risk/BTCUSDT/potential_model/initial_action_2/model_0.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_2/model_1.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_2/model_2.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_2/model_3.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_2/model_4.pth",
                ],
                3: [
                    "result_risk/BTCUSDT/potential_model/initial_action_3/model_0.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_3/model_1.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_3/model_2.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_3/model_3.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_3/model_4.pth",
                ],
                4: [
                    "result_risk/BTCUSDT/potential_model/initial_action_4/model_0.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_4/model_1.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_4/model_2.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_4/model_3.pth",
                    "result_risk/BTCUSDT/potential_model/initial_action_4/model_4.pth",
                ],
            }
        elif args.dataset_name == "ETHUSDT":
            model_path_list_dict = {
                0: [
                    "result_risk/ETHUSDT/potential_model/initial_action_0/model_0.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_0/model_1.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_0/model_2.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_0/model_3.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_0/model_4.pth",
                ],
                1: [
                    "result_risk/ETHUSDT/potential_model/initial_action_1/model_0.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_1/model_1.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_1/model_2.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_1/model_3.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_1/model_4.pth",
                ],
                2: [
                    "result_risk/ETHUSDT/potential_model/initial_action_2/model_0.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_2/model_1.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_2/model_2.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_2/model_3.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_2/model_4.pth",
                ],
                3: [
                    "result_risk/ETHUSDT/potential_model/initial_action_3/model_0.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_3/model_1.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_3/model_2.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_3/model_3.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_3/model_4.pth",
                ],
                4: [
                    "result_risk/ETHUSDT/potential_model/initial_action_4/model_0.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_4/model_1.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_4/model_2.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_4/model_3.pth",
                    "result_risk/ETHUSDT/potential_model/initial_action_4/model_4.pth",
                ],
            }
        elif args.dataset_name == "GALAUSDT":
            model_path_list_dict = {
                0: [
                    "result_risk/GALAUSDT/potential_model/initial_action_0/model_0.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_0/model_1.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_0/model_2.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_0/model_3.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_0/model_4.pth",
                ],
                1: [
                    "result_risk/GALAUSDT/potential_model/initial_action_1/model_0.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_1/model_1.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_1/model_2.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_1/model_3.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_1/model_4.pth",
                ],
                2: [
                    "result_risk/GALAUSDT/potential_model/initial_action_2/model_0.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_2/model_1.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_2/model_2.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_2/model_3.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_2/model_4.pth",
                ],
                3: [
                    "result_risk/GALAUSDT/potential_model/initial_action_3/model_0.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_3/model_1.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_3/model_2.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_3/model_3.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_3/model_4.pth",
                ],
                4: [
                    "result_risk/GALAUSDT/potential_model/initial_action_4/model_0.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_4/model_1.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_4/model_2.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_4/model_3.pth",
                    "result_risk/GALAUSDT/potential_model/initial_action_4/model_4.pth",
                ],
            }
        elif args.dataset_name == "BTCTUSD":
            model_path_list_dict = {
                0: [
                    "result_risk/BTCTUSD/potential_model/initial_action_0/model_0.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_0/model_1.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_0/model_2.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_0/model_3.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_0/model_4.pth",
                ],
                1: [
                    "result_risk/BTCTUSD/potential_model/initial_action_1/model_0.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_1/model_1.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_1/model_2.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_1/model_3.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_1/model_4.pth",
                ],
                2: [
                    "result_risk/BTCTUSD/potential_model/initial_action_2/model_0.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_2/model_1.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_2/model_2.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_2/model_3.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_2/model_4.pth",
                ],
                3: [
                    "result_risk/BTCTUSD/potential_model/initial_action_3/model_0.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_3/model_1.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_3/model_2.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_3/model_3.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_3/model_4.pth",
                ],
                4: [
                    "result_risk/BTCTUSD/potential_model/initial_action_4/model_0.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_4/model_1.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_4/model_2.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_4/model_3.pth",
                    "result_risk/BTCTUSD/potential_model/initial_action_4/model_4.pth",
                ],
            }
        self.model_path_list_dict = model_path_list_dict
        self.num_model = len(self.model_path_list_dict[0])
        self.max_holding_number = args.max_holding_number
        self.action_dim = args.action_dim
        self.transcation_cost = args.transcation_cost
        self.back_time_length = args.back_time_length

        # RL setting

        self.high_level_tech_indicator_list = np.load(
            "data/feature/minitue_feature.npy"
        ).tolist()
        self.low_level_tech_indicator_list = np.load(
            "data/feature/second_feature.npy"
        ).tolist()
        self.n_state = len(self.high_level_tech_indicator_list)

        self.action = args.action
        self.test_df_list = [
            pd.read_feather(args.valid_data_path),
            pd.read_feather(args.test_data_path),
        ]
        self.save_path = os.path.join(
            args.save_path, "single_agent_{}".format(self.action)
        )

    def test(self):
        for label, df in zip(["valid", "test"], self.test_df_list):
            self.test_env_instance = high_level_testing_env(
                df=df,
                transcation_cost=self.transcation_cost,
                back_time_length=self.back_time_length,
                max_holding_number=self.max_holding_number,
                action_dim=self.action_dim,
                early_stop=0,
                initial_action=0,
                model_path_list_dict=self.model_path_list_dict,
            )
            s, info = self.test_env_instance.reset()
            done = False
            action_list = []
            reward_list = []
            while not done:
                a = self.action
                s_, r, done, info_ = self.test_env_instance.step(a)
                reward_list.append(r)
                s = s_
                info = info_
                action_list.append(a)
            action_list = np.array(action_list)
            reward_list = np.array(reward_list)
            if not os.path.exists(os.path.join(self.save_path, label)):
                os.makedirs(os.path.join(self.save_path, label))
            np.save(os.path.join(self.save_path, label, "action.npy"), action_list)
            np.save(os.path.join(self.save_path, label, "reward.npy"), reward_list)
            np.save(
                os.path.join(self.save_path, label, "final_balance.npy"),
                self.test_env_instance.final_balance,
            )
            np.save(
                os.path.join(self.save_path, label, "pure_balance.npy"),
                self.test_env_instance.pured_balance,
            )
            np.save(
                os.path.join(self.save_path, label, "require_money.npy"),
                self.test_env_instance.required_money,
            )
            np.save(
                os.path.join(self.save_path, label, "commission_fee_history.npy"),
                self.test_env_instance.comission_fee_history,
            )
            np.save(
                os.path.join(self.save_path, label, "macro_reward_history.npy"),
                self.test_env_instance.macro_reward_history,
            )
            get_test_contrast_curve_high_level(
                df,
                os.path.join(self.save_path, label, "result.pdf"),
                reward_list,
                self.test_env_instance.required_money,
            )
            get_test_contrast_curve(
                df,
                os.path.join(self.save_path, label, "micro_result.pdf"),
                self.test_env_instance.macro_reward_history,
                self.test_env_instance.required_money,
            )


if __name__ == "__main__":
    args = parser.parse_args()
    agent = trader(args)
    agent.test()
