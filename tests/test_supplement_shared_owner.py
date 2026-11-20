"""A new case may cover an existing co-implementer without moving ownership."""
from test_supplemental_frozen_coverage import module,case
import pytest


def test_new_case_can_include_the_existing_recommendation_service_owner():
    old,new,paths=case();record={'id':'RECORDS','role':'impl','owns':['Runtime/Records.cs'],'acceptance':[],'instructions':'fixed'}
    old['units'].append(record);new['units'].append(record|{'acceptance':['New']})
    new['test_links'][-1]['implementing_units']=['SHELL','RECORDS']
    module().validate_supplement(old,new,'digest','TEST',paths,'New','Old',implementers=['SHELL','RECORDS'])


def test_new_mapping_cannot_remove_a_preexisting_implementer():
    old,new,paths=case()
    with pytest.raises(ValueError):module().validate_supplement(old,new,'digest','TEST',paths,'New','Old',implementers=[])
