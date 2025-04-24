-- Install Array Modifier menu item if not already there

fn MaybeInstallArrayModifierMenuItem mainMenuBar =
(
    numMenus = mainMenuBar.numItems()
    for i = 1 to numMenus do
    (
        menu = (mainmenubar.getitem i).GetSubMenu()
        menuTitle = menu.gettitle()
        if(menuTitle == ~ARRAY_MENU_CATEGORY~) do
        (
            -- Got the Modifiers menu
            
            -- Look for the "Parametric Deformers" submenu
            numItems = menu.numItems()
            for item = 1 to numItems do
            (
                -- If the Parametric Deformers menu is there, drill into it
                if((menu.GetItem item).getTitle() == ~PARAMETRIC_DEFORMERS_MENU_CATEGORY~) do
                (
                    PDMenu = (menu.GetItem item).GetSubMenu()
                    
                    -- Look for the "Array" modifier entry. If there, return success code,
                    -- otherwise try to insert it
                    numPDItems = PDMenu.numItems()
                    for PDItem = 1 to numPDItems do
                    (
                        PDItemTitle = (PDMenu.GetItem PDItem).getTitle()
                        if(PDItemTitle == ~ARRAYMODIFIER_NAME~) do
                        (
                            format "Array modifier menu already installed\n"
                            return true
                        )
                        
                        -- If we find the Bend modifier, insert it there
                        if(PDItemTitle == ~BENDMODIFIER_NAME~) do
                        (
                            -- Create and add the menu item
                            arrayItem = menuMan.createActionItem "ArrayModifier" "Modifiers"
                            if(arrayItem != undefined) do
                            (
                                PDMenu.addItem arrayItem PDItem
                                menuMan.updateMenuBar()
                                return true
                            )
                        )
                    )
                )
            )
        )
    )
    return false
)

mainMenuBar = menuMan.getMainMenuBar()
if (mainMenuBar != undefined) then (MaybeInstallArrayModifierMenuItem mainMenuBar)

-------BEGIN-SIGNATURE-----
-- TQoAADCCCkkGCSqGSIb3DQEHAqCCCjowggo2AgEBMQ8wDQYJKoZIhvcNAQELBQAw
-- CwYJKoZIhvcNAQcBoIIHZTCCB2EwggVJoAMCAQICEAf+q645FYLSHMpcP88Z7u0w
-- DQYJKoZIhvcNAQELBQAwaTELMAkGA1UEBhMCVVMxFzAVBgNVBAoTDkRpZ2lDZXJ0
-- LCBJbmMuMUEwPwYDVQQDEzhEaWdpQ2VydCBUcnVzdGVkIEc0IENvZGUgU2lnbmlu
-- ZyBSU0E0MDk2IFNIQTM4NCAyMDIxIENBMTAeFw0yNDAxMjkwMDAwMDBaFw0yNTAx
-- MjgyMzU5NTlaMGkxCzAJBgNVBAYTAlVTMRMwEQYDVQQIEwpDYWxpZm9ybmlhMRMw
-- EQYDVQQHEwpTYW4gUmFmYWVsMRcwFQYDVQQKEw5BdXRvZGVzaywgSW5jLjEXMBUG
-- A1UEAxMOQXV0b2Rlc2ssIEluYy4wggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIK
-- AoICAQC0RxrB/ltX22+FLPkE5TvZGoUNMh4MS8IuVzCX1frS9SXLKfVSvPbK2hko
-- NL5h4OEKFDZwdgkjQWUtqGeJofdPN4wDkR/OPz/1bYuHCLtVBcBTQsZ7NlmHaJX0
-- hsDJrItSjDgocxuxvioKBwqvmXwAJ4fbvOuNx73MkuyU8w8ZeSjtWZM3FENRzjoV
-- JgwJerWJbVkpxKTU80tsOSTzZ8WvYp1M6/0joYD5+VH88YUSYLMWiNTJSWubZGAS
-- sNDkAgyHu3JaVStUskhv9NAlnhJaq5lSZFEqpc80noAlxQOYQyJlD1J5Mn+z6AUF
-- L9Rd3AYw0ofXYh8fFWqnwFjrS/XKqixdF7nt5enEJPfkEkNqTJEdyeFy/fu9SQ8M
-- S1KfYugbtnyEv1ycIwWQepN4TxuKi/R3sL7xczeKu+1RhrjBGoWNztWFxqGVDhbA
-- OuUtWN5qF7BWvIyQ91YbNIcmvvB5TkFgwZKZjNnydik317UB50qbHXMx8Az2+07s
-- zl4wkDVp9p3Bli01iPZn/oQceRse33o/Uomab5cezVB5nvsGILwUhHSH5C30Oj3U
-- /Y6bCSjzIYV8jDcJBb9MN9mvDGuMW+hu68bcW7N/6ZopHzV1mnev4yH3wSTV595c
-- twUVl+axNVAE0qR9NzXFze1TcZ9qnuQPU8s9KDRrih7lJSrCmQIDAQABo4ICAzCC
-- Af8wHwYDVR0jBBgwFoAUaDfg67Y7+F8Rhvv+YXsIiGX0TkIwHQYDVR0OBBYEFLvQ
-- k6uXtIxMbptXKFi9ul6yfaHsMD4GA1UdIAQ3MDUwMwYGZ4EMAQQBMCkwJwYIKwYB
-- BQUHAgEWG2h0dHA6Ly93d3cuZGlnaWNlcnQuY29tL0NQUzAOBgNVHQ8BAf8EBAMC
-- B4AwEwYDVR0lBAwwCgYIKwYBBQUHAwMwgbUGA1UdHwSBrTCBqjBToFGgT4ZNaHR0
-- cDovL2NybDMuZGlnaWNlcnQuY29tL0RpZ2lDZXJ0VHJ1c3RlZEc0Q29kZVNpZ25p
-- bmdSU0E0MDk2U0hBMzg0MjAyMUNBMS5jcmwwU6BRoE+GTWh0dHA6Ly9jcmw0LmRp
-- Z2ljZXJ0LmNvbS9EaWdpQ2VydFRydXN0ZWRHNENvZGVTaWduaW5nUlNBNDA5NlNI
-- QTM4NDIwMjFDQTEuY3JsMIGUBggrBgEFBQcBAQSBhzCBhDAkBggrBgEFBQcwAYYY
-- aHR0cDovL29jc3AuZGlnaWNlcnQuY29tMFwGCCsGAQUFBzAChlBodHRwOi8vY2Fj
-- ZXJ0cy5kaWdpY2VydC5jb20vRGlnaUNlcnRUcnVzdGVkRzRDb2RlU2lnbmluZ1JT
-- QTQwOTZTSEEzODQyMDIxQ0ExLmNydDAJBgNVHRMEAjAAMA0GCSqGSIb3DQEBCwUA
-- A4ICAQBW3pC8sfzMhKHTYPYe6UqU0IX/tPfIFJNdtGQoeYdBBjbLAowcdlzQ1KLM
-- 9HC/93aXV9q8iONYwFY8oajmFASaNc6Zk7vZQTPA8ug96a8ynTWXsdasfTYK9z0U
-- JF6J8jg/NJMHQq8lx0RX3JtyfJpf5JDll6M6h5B3FhN/QtBaRTNJ+DT8hjQ0p+eu
-- fYJmnWH1GyiVmLTGnM0KnMFLplpNrPDiE5iVy7B+lynlR27oKvc+NZD8O2Ly/KSO
-- ayY7paYZd/tH+nU6E2w4qy8CNclXlVxPFf2dt41Nik6slu/rQSVnjRJ/EKvOIOrQ
-- 0nPUAx3oNUkgHtDO8/jnZ06H/bUMUvtmp96RIyzYXPfCfKKlzRvvpwNOUPuN9+ka
-- 6JyN2iNpe/ZNH41YGMFvr/y9pg+qN1lYhsjvA6+uVKFbIerPFdJ9gSpRzpmFQUHh
-- 11DHn6OPnO/hCJyWg50uDhQ9C7nvVRbsoZ/2Hz9uwUKcJiBE8RTFK4hvopa/nVSi
-- eiKQwyadDgwRkKmPSB3ezKXDeYU3TOG7ugP9WHLgUIL20hKhN5nGom8REHPsCJI7
-- xewV44xlWDOu5/00WH9Y70s4qvXjQchpGMEluCyj3jKpYVxPO1cUnGl+8l03Ntdu
-- 80MDBkfVy9kc9SAvG0wxas1/UM7SUNa0gl7M+mkRue0rjKRqOzGCAqgwggKkAgEB
-- MH0waTELMAkGA1UEBhMCVVMxFzAVBgNVBAoTDkRpZ2lDZXJ0LCBJbmMuMUEwPwYD
-- VQQDEzhEaWdpQ2VydCBUcnVzdGVkIEc0IENvZGUgU2lnbmluZyBSU0E0MDk2IFNI
-- QTM4NCAyMDIxIENBMQIQB/6rrjkVgtIcylw/zxnu7TANBgkqhkiG9w0BAQsFADAN
-- BgkqhkiG9w0BAQEFAASCAgALVJ/fu1RwPe253wr98MgMl5UhQjcT6VKdmZqolZhg
-- CRyp0b9VhVSB/mlCYfcEab0Di8Hzzaw5SH59SPjy7oqcVWhtKnYJKMzfjQmnHI2h
-- oLD90p1pP9iALfLR/53qR1DBNEA4p9R3HKcVMy3ODY5VCIKysMzkboGamotccjQo
-- xlSpvK0cgqtJ3Q/odSEKquN0KQga7hn0mnRVstdJA8QLFxT47D4f6/sGJ92kCVk8
-- oi8CFDn3ZSEhc07pYQZpYGSksUUbpRyHyoCQ6hNFZ7mOdYd5vg2TL86MMB7+sE3a
-- BoNHaPH1SsYuKPiD0czcw23lQW7aXe9beyL5dUBvhDU+HP5ssZ83zUtH9JV1bgbN
-- JsRi8B+0C01zd3jcBuLWgcbPzmWG6O17utpPkcEZ9ftPw+RmCCE7N58mZhI2xVfP
-- BiTAp8HFrPlo98GiYDj+GjrR28j/cWoPC9QhrlSmi4Ro/zJ5Q8kvT7kBLWtv+apd
-- ihNb8ojEg1iDZRZMYwL5QU+VIJbnHr+1ZQVQJgCstRrF4TAUq+T4yKQoBWlhtYGj
-- 4066505Q8MWAqPral8lVSIZt7SGR3fbYLbJouYGcjArgA5i2vZdHONBMOcQCk+Z7
-- 2Ww5L4JLEdPSlZmfrC6k68ClQ+4hYP8+UOn9pvmvIcjGN8rE3TivQQu/GHI/ahRC
-- ug==
-- -----END-SIGNATURE-----