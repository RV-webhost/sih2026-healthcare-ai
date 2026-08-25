import uuid


def test_bed_availability_counts(client, seed_wards_and_beds):
    """Test correct total and available bed counts are returned."""
    response = client.get("/api/v1/beds/availability")
    assert response.status_code == 200

    json_data = response.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["total_beds"] == 2
    assert json_data["data"]["available_beds"] == 2
    assert json_data["data"]["occupied_beds"] == 0


def test_bed_availability_ward_filter(client, seed_wards_and_beds):
    """Test filtering bed availability by ward type."""
    response = client.get("/api/v1/beds/availability?ward=ICU")
    assert response.status_code == 200

    json_data = response.get_json()
    assert json_data["data"]["ward_filter"] == "ICU"
    assert json_data["data"]["total_beds"] == 1
    assert json_data["data"]["available_beds"] == 1
    assert json_data["data"]["beds"][0]["bed_number"] == "ICU-101"


def test_allocate_bed_success(client, seed_wards_and_beds, mock_patient_id):
    """Test available bed can be successfully allocated and status changes to OCCUPIED."""
    payload = {
        "patient_id": str(mock_patient_id),
        "ward_type": "ICU"
    }
    response = client.post("/api/v1/beds/allocate", json=payload)
    assert response.status_code == 201

    json_data = response.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["bed"]["status"] == "OCCUPIED"
    assert json_data["data"]["allocation"]["status"] == "ACTIVE"
    assert json_data["data"]["allocation"]["patient_id"] == str(mock_patient_id)

    # Verify availability count decreased
    avail_res = client.get("/api/v1/beds/availability?ward=ICU")
    assert avail_res.get_json()["data"]["available_beds"] == 0
    assert avail_res.get_json()["data"]["occupied_beds"] == 1


def test_allocate_bed_unavailable(client, seed_wards_and_beds, mock_patient_id):
    """Test allocating when no beds are available returns BED_UNAVAILABLE."""
    # Allocate the only available ICU bed
    client.post("/api/v1/beds/allocate", json={
        "patient_id": str(mock_patient_id),
        "ward_type": "ICU"
    })

    # Second patient attempts to allocate in ICU
    res = client.post("/api/v1/beds/allocate", json={
        "patient_id": str(uuid.uuid4()),
        "ward_type": "ICU"
    })
    assert res.status_code == 409

    json_data = res.get_json()
    assert json_data["success"] is False
    assert json_data["error_code"] == "BED_UNAVAILABLE"


def test_release_bed(client, seed_wards_and_beds, mock_patient_id):
    """Test releasing a bed closes allocation and sets status back to AVAILABLE."""
    # Allocate bed
    alloc_res = client.post("/api/v1/beds/allocate", json={
        "patient_id": str(mock_patient_id),
        "ward_type": "ICU"
    })
    bed_id = alloc_res.get_json()["data"]["bed"]["id"]

    # Release bed
    release_res = client.patch(f"/api/v1/beds/{bed_id}/release")
    assert release_res.status_code == 200

    json_data = release_res.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["bed"]["status"] == "AVAILABLE"
    assert json_data["data"]["allocation"]["status"] == "RELEASED"
    assert json_data["data"]["allocation"]["released_at"] is not None

    # Verify availability
    avail_res = client.get("/api/v1/beds/availability?ward=ICU")
    assert avail_res.get_json()["data"]["available_beds"] == 1


def test_release_unoccupied_bed(client, seed_wards_and_beds):
    """Test releasing an already available bed returns 400 BED_NOT_OCCUPIED."""
    bed_id = seed_wards_and_beds["icu_bed_id"]
    response = client.patch(f"/api/v1/beds/{bed_id}/release")
    assert response.status_code == 400
    assert response.get_json()["error_code"] == "BED_NOT_OCCUPIED"


def test_get_bed_by_id(client, seed_wards_and_beds):
    """Test retrieving bed by ID."""
    bed_id = seed_wards_and_beds["icu_bed_id"]
    response = client.get(f"/api/v1/beds/{bed_id}")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["bed_number"] == "ICU-101"
    assert data["ward"]["ward_type"] == "ICU"
