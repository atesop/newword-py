# -*- coding: utf-8 -*-
"""测试公共 fixtures"""

import os

import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def fixtures_dir():
    """返回测试数据目录路径"""
    return FIXTURES_DIR


@pytest.fixture
def sample_corpus_path(fixtures_dir):
    """返回示例语料文件路径"""
    return os.path.join(fixtures_dir, "sample_corpus.txt")


@pytest.fixture
def test_config_path(fixtures_dir):
    """返回测试配置文件路径"""
    return os.path.join(fixtures_dir, "test.conf")


@pytest.fixture
def test_punct_path(fixtures_dir):
    """返回测试标点文件路径"""
    return os.path.join(fixtures_dir, "test_punct.dat")


@pytest.fixture
def golden_output_path(fixtures_dir):
    """返回 golden output 文件路径"""
    return os.path.join(fixtures_dir, "golden_output.csv")
