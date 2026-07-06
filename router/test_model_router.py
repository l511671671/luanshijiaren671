"""
ModelRouter 测试用例

运行方式：
  python router/test_model_router.py
  python router/test_model_router.py  -- 全部测试

也可通过 pytest 运行：
  pytest router/test_model_router.py -v
"""

import sys
from model_router import (
    ModelRouter,
    ModelConfig,
    TaskTier,
    DEFAULT_MODELS,
)


def test_classify_light():
    router = ModelRouter()
    cases = [
        "把这段文字翻译一下",
        "总结一下这篇文章",
        "format this json",
        "解释一下什么叫换手率",
    ]
    for c in cases:
        result = router.route(c)
        assert result.tier == TaskTier.TIER_1_LIGHT, f"{c} -> {result.tier}"
        assert result.selected.tier == "light", f"{c} 未路由到轻量模型"
    print("[OK] test_classify_light passed")


def test_classify_standard():
    router = ModelRouter()
    cases = [
        "帮我写一段 Python 脚本读取 CSV",
        "生成一份房产营销文档",
        "写一个交易提醒模块",
    ]
    for c in cases:
        result = router.route(c)
        assert result.tier in (TaskTier.TIER_2_STANDARD, TaskTier.TIER_3_COMPLEX), f"{c} -> {result.tier}"
        assert result.selected.tier in ("standard", "light"), f"{c} 路由到了不合适的模型"
    print("[OK] test_classify_standard passed")


def test_classify_complex():
    router = ModelRouter()
    cases = [
        "帮我设计一个 A 股交易系统的架构",
        "对比两种房产租赁方案",
        "需要跨会话的长期任务，先写个 checkpoint 方案",
        "把下面 5 个文件重构一下",
    ]
    for c in cases:
        result = router.route(c)
        assert result.tier == TaskTier.TIER_3_COMPLEX, f"{c} -> {result.tier}"
        assert result.selected.tier in ("complex", "standard"), f"{c} 未路由到高阶模型"
    print("[OK] test_classify_complex passed")


def test_classify_verify():
    router = ModelRouter()
    cases = [
        "帮我复核这份交易计划",
        "检查一下代码有没有 bug",
        "验证一下风控条件",
        "review 这份文档",
    ]
    for c in cases:
        result = router.route(c)
        assert result.tier == TaskTier.TIER_4_VERIFY, f"{c} -> {result.tier}"
    print("[OK] test_classify_verify passed")


def test_fallback_chain_exists():
    router = ModelRouter()
    result = router.route("帮我设计一个交易系统")
    assert len(result.fallback_chain) > 0, "fallback 链不能为空"
    # 主模型不应出现在 fallback 链中
    assert result.selected.id not in [m.id for m in result.fallback_chain]
    print("[OK] test_fallback_chain_exists passed")


def test_fallback_skip_failed_models():
    router = ModelRouter()
    result = router.route_with_fallback("检查代码", attempt_results=["deepseek-r1"])
    ids = [m.id for m in result.fallback_chain]
    assert "deepseek-r1" not in ids, "已失败模型应被跳过"
    print("[OK] test_fallback_skip_failed_models passed")


def test_empty_pool_raises():
    try:
        router = ModelRouter(models=[])
        router.route("任意请求")
        assert False, "空模型池应抛出异常"
    except ValueError:
        pass
    print("[OK] test_empty_pool_raises passed")


def test_custom_classifier():
    """允许注入自定义分类器"""
    def always_verify(prompt: str) -> TaskTier:
        return TaskTier.TIER_4_VERIFY

    router = ModelRouter(classifier=always_verify)
    result = router.route("你好")
    assert result.tier == TaskTier.TIER_4_VERIFY
    print("[OK] test_custom_classifier passed")


def test_json_serialization():
    """结果可以序列化为 JSON"""
    import json
    router = ModelRouter()
    result = router.route("验证一下")
    d = result.to_dict()
    assert "tier" in d and "selected" in d and "fallback_chain" in d
    json.dumps(d)  # 不应抛异常
    print("[OK] test_json_serialization passed")


def run_all_tests():
    test_classify_light()
    test_classify_standard()
    test_classify_complex()
    test_classify_verify()
    test_fallback_chain_exists()
    test_fallback_skip_failed_models()
    test_empty_pool_raises()
    test_custom_classifier()
    test_json_serialization()
    print("\n[ALL PASSED] all tests passed")


if __name__ == "__main__":
    run_all_tests()
