import pytest

from helpers import assert_finite


def _assert_json_response(response):
    assert response.status_code == 200, response.text
    assert response.headers.get("content-type", "").startswith("application/json")
    return response.json()


def test_ipr_returns_json_curve(client, ipr_url, ipr_request, stack):
    data = _assert_json_response(
        client.post(f"{ipr_url}/ipr/calc", json=ipr_request)
    )

    assert isinstance(data, dict)
    assert isinstance(data.get("q_liq"), list)
    assert isinstance(data.get("p_wf"), list)
    assert len(data["q_liq"]) == len(data["p_wf"])
    assert len(data["q_liq"]) == 21

    assert_finite(data["q_liq"], "q_liq")
    assert_finite(data["p_wf"], "p_wf")
    assert all(value >= 0 for value in data["q_liq"])
    assert all(value > 0 for value in data["p_wf"])


def test_ipr_custom_points(client, ipr_url, ipr_request, stack):
    request = dict(ipr_request, points=41)

    data = _assert_json_response(
        client.post(f"{ipr_url}/ipr/calc", json=request)
    )

    assert len(data["q_liq"]) == 41
    assert len(data["p_wf"]) == 41
    assert data["p_wf"][0] == pytest.approx(1.0, abs=0.01)
    assert data["p_wf"][-1] == pytest.approx(request["p_res"], abs=0.01)
    assert data["q_liq"][-1] == pytest.approx(0.0, abs=0.1)


def test_vlp_returns_json_curve(client, vlp_url, vlp_request, stack):
    data = _assert_json_response(
        client.post(f"{vlp_url}/vlp/calc", json=vlp_request)
    )

    assert isinstance(data, dict)
    assert isinstance(data.get("q_liq"), list)
    assert isinstance(data.get("p_wf"), list)
    assert len(data["q_liq"]) == len(data["p_wf"])
    assert len(data["q_liq"]) == 21

    assert_finite(data["q_liq"], "q_liq")
    assert_finite(data["p_wf"], "p_wf")
    assert all(value >= 0 for value in data["q_liq"])
    assert all(value > 0 for value in data["p_wf"])
    assert all(
        data["q_liq"][index] < data["q_liq"][index + 1]
        for index in range(len(data["q_liq"]) - 1)
    )


def test_nodal_returns_json_point(client, nodal_url, nodal_request, stack):
    data = _assert_json_response(
        client.post(f"{nodal_url}/nodal/calc", json=nodal_request)
    )

    assert isinstance(data, list)
    assert len(data) == 1

    point = data[0]
    assert isinstance(point, dict)
    assert set(point) >= {"q_liq", "p_wf"}
    assert_finite([point["q_liq"], point["p_wf"]], "nodal point")
    assert point["q_liq"] >= 0
    assert point["p_wf"] > 0
