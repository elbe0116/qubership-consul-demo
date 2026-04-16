*** Variables ***
${MONITORED_IMAGES}         %{MONITORED_IMAGES}

*** Settings ***
Resource  ../../shared/keywords.robot

*** Keywords ***
# FIX for AWS deployment: use ${parts[-1]} (last element) instead of ${parts[2]}
# This handles both formats:
#   - "hashicorp/consul:1.21.5" → 2 parts → [-1] = tag
#   - "registry:port/image:tag" → 3 parts → [-1] = tag
# Original code with ${parts[2]} only works for images with registry port
Get Image Tag
    [Arguments]  ${image}
    ${parts}=  Split String  ${image}  :
    ${length}=  Get Length  ${parts}
    Run Keyword If  ${length} > 1  Return From Keyword  ${parts}[-1]
    Run Keywords
    ...  Log To Console  \n[ERROR] Image ${parts} has no tag: ${image}\nMonitored images list: ${MONITORED_IMAGES}
    ...  AND  Fail  Some images were not found, please check your .helpers template and description.yaml in the repository

*** Test Cases ***
Test Hardcoded Images
  [Tags]  consul_images
  ${stripped_resources}=  Strip String  ${MONITORED_IMAGES}  characters=,  mode=right
  @{list_resources} =  Split String	${stripped_resources} 	,
  FOR  ${resource}  IN  @{list_resources}
    ${type}  ${name}  ${container_name}  ${image}=  Split String  ${resource}
    ${resource_image}=  Get Resource Image  ${type}  ${name}  %{CONSUL_NAMESPACE}  ${container_name}

    ${expected_tag}=  Get Image Tag  ${image}
    ${actual_tag}=    Get Image Tag  ${resource_image}

    Log To Console  \n[COMPARE] ${resource}: Expected tag = ${expected_tag}, Actual tag = ${actual_tag}

    Run Keyword And Continue On Failure  Should Be Equal   ${actual_tag}   ${expected_tag}
    
  END
