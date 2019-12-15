import datetime
from uuid import UUID

import pytest

from apd.aggregation.query import (
    get_data,
    get_deployment_ids,
    db_session_var,
)


class TestGetData:
    @pytest.fixture
    def mut(self):
        return get_data

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "filter,num_items_expected",
        [
            ({}, 9),
            ({"sensor_name": "Test"}, 7),
            ({"deployment_id": UUID("b4c68905-b1e4-4875-940e-69e5d27730fd")}, 5),
            ({"collected_after": datetime.datetime(2020, 4, 1, 12, 2, 1)}, 3),
            ({"collected_before": datetime.datetime(2020, 4, 1, 12, 2, 1)}, 4),
            (
                {
                    "collected_after": datetime.datetime(2020, 4, 1, 12, 2, 1),
                    "collected_before": datetime.datetime(2020, 4, 1, 12, 3, 5),
                },
                2,
            ),
        ],
    )
    async def test_iterate_over_items(
        self, mut, db_session, populated_db, filter, num_items_expected
    ):
        db_session_var.set(db_session)
        points = [dp async for dp in mut(**filter)]
        assert len(points) == num_items_expected

    @pytest.mark.asyncio
    async def test_empty_db(self, mut, db_session, migrated_db):
        db_session_var.set(db_session)
        points = [dp async for dp in mut()]
        assert len(points) == 0


class TestGetDeployments:
    @pytest.fixture
    def mut(self):
        return get_deployment_ids

    @pytest.mark.asyncio
    async def test_get_all_deployments(self, mut, db_session, populated_db):
        db_session_var.set(db_session)
        deployment_ids = await mut()
        assert set(deployment_ids) == {
            UUID("b4c68905-b1e4-4875-940e-69e5d27730fd"),
            UUID("6e887b81-57c3-4f3b-a7e7-bad159e05e78"),
        }

    @pytest.mark.asyncio
    async def test_empty_db(self, mut, db_session, migrated_db):
        db_session_var.set(db_session)
        deployment_ids = await mut()
        assert deployment_ids == []
