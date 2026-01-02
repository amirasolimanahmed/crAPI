*** Settings ***
Library    RequestsLibrary

*** Variables ***
${BASE_URL}    %{BASE_URL=http://localhost:8888}

*** Test Cases ***
Login With Invalid Password Should Return 401
    Create Session    api    ${BASE_URL}

    ${payload}=    Create Dictionary    email=test@test.com    password=wrong

    # IMPORTANT: allow_expected=True prevents RequestsLibrary from raising HTTPError on 4xx/5xx
    ${resp}=    Post On Session
    ...    api
    ...    /identity/api/auth/login
    ...    json=${payload}
    ...    expected_status=ANY

    Should Be Equal As Integers    ${resp.status_code}    401
