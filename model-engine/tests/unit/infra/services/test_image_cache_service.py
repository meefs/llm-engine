from typing import Any

import pytest
from model_engine_server.common.config import hmi_config
from model_engine_server.common.env_vars import GIT_TAG
from model_engine_server.core.config import infra_config
from model_engine_server.infra.services.image_cache_service import DockerImage, ImageCacheService


@pytest.mark.asyncio
async def test_image_cache_success(
    fake_image_cache_service: ImageCacheService,
    model_endpoint_1,
    model_endpoint_2,
    model_endpoint_3,
    model_endpoint_4,
):
    infra_states = {
        model_endpoint_1.record.id: (bool, model_endpoint_1.infra_state),
        model_endpoint_2.record.id: (bool, model_endpoint_2.infra_state),
        model_endpoint_3.record.id: (bool, model_endpoint_3.infra_state),
        model_endpoint_4.record.id: (bool, model_endpoint_4.infra_state),
    }
    repo: Any = fake_image_cache_service.model_endpoint_record_repository
    repo.add_model_endpoint_record(model_endpoint_1.record)
    repo.add_model_endpoint_record(model_endpoint_2.record)
    repo.add_model_endpoint_record(model_endpoint_3.record)
    repo.add_model_endpoint_record(model_endpoint_4.record)

    await fake_image_cache_service.execute(infra_states)  # type: ignore
    gateway: Any = fake_image_cache_service.image_cache_gateway

    assert (
        f"{infra_config().ml_account_id}.dkr.ecr.us-west-2.amazonaws.com/my-repo:abcdefg222"
        in gateway.cached_images["t4"]
    )
    assert (
        f"{infra_config().ml_account_id}.dkr.ecr.us-west-2.amazonaws.com/my-repo:abcdefg111111111"
        in gateway.cached_images["t4"]
    )
    assert (
        f"{infra_config().ml_account_id}.dkr.ecr.us-west-2.amazonaws.com/my-repo:abcdefg00000"
        in gateway.cached_images["t4"]
    )


@pytest.mark.asyncio
async def test_caching_finetune_llm_images(
    fake_image_cache_service: ImageCacheService,
):
    await fake_image_cache_service.execute({})
    gateway: Any = fake_image_cache_service.image_cache_gateway

    istio_image = DockerImage("gcr.io/istio-release/proxyv2", "1.15.0")
    tgi_image_110 = DockerImage(
        f"{infra_config().docker_repo_prefix}/{hmi_config.tgi_repository}", "1.1.0"
    )
    vllm_image_027 = DockerImage(
        f"{infra_config().docker_repo_prefix}/{hmi_config.vllm_repository}", "0.2.7"
    )
    vllm_image_032 = DockerImage(
        f"{infra_config().docker_repo_prefix}/{hmi_config.vllm_repository}", "0.3.2"
    )
    latest_tag = "fake_docker_repository_latest_image_tag"
    vllm_batch_image_latest = DockerImage(
        f"{infra_config().docker_repo_prefix}/{hmi_config.batch_inference_vllm_repository}",
        latest_tag,
    )
    forwarder_image = DockerImage(f"{infra_config().docker_repo_prefix}/model-engine", GIT_TAG)

    for key in ["a10", "a100", "h100", "h100_3g40gb", "h100_1g20gb"]:
        for llm_image in [
            istio_image,
            tgi_image_110,
            vllm_image_027,
            vllm_image_032,
            vllm_batch_image_latest,
            forwarder_image,
        ]:
            assert f"{llm_image.repo}:{llm_image.tag}" in gateway.cached_images[key]
