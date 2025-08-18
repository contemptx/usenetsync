#include <stdio.h>
#include <stdlib.h>

// Support Unicode compilation and non-Windows compilation
#ifdef _WIN32
#    include <tchar.h>
#else
#    define _T(x) x
typedef char TCHAR;
#endif

// To use the static version of TurboActivate then uncomment the next line
//#define TURBOACTIVATE_STATIC

// Include the correct library on Windows
#ifdef TURBOACTIVATE_STATIC
#    ifdef _DEBUG
#        ifdef _DLL
#            pragma comment(lib, "TurboActivate-MDd.lib")
#        else
#            pragma comment(lib, "TurboActivate-MTd.lib")
#        endif
#    else
#        ifdef _DLL
#            pragma comment(lib, "TurboActivate-MD.lib")
#        else
#            pragma comment(lib, "TurboActivate-MT.lib")
#        endif
#    endif
#else
#    pragma comment(lib, "TurboActivate.lib")
#endif


#include "TurboActivate.h"

/* The handle used for TurboActivate function calls. */
uint32_t taHandle;


/*
   This function will be called by a separate background thread to notify
   your app of trial expiration (either naturally, or because of customer fraud).

   That means if you're displaying UI to your users you must ensure
   that any windows (or any resource sharing for that matter) are
   created in the right thread context or bad things might happen.
   Test this behavior well before releasing to your end-users.
*/
void TA_CC trialCallback(uint32_t status, void * userDefinedPtr)
{
    switch (status)
    {
        case TA_CB_EXPIRED:
            //TODO: disallow any features in your app.
            printf("The app trial period has expired\n");
            break;

        case TA_CB_EXPIRED_FRAUD:
            //TODO: disallow any features in your app.
            printf("The app trial has expired due to date/time fraud\n");
            break;

        default:
            printf("The app trial callback returned an unexpected status: %d\n", (int)status);
            break;
    }
}


int main(int argc, char ** argv)
{
    // Set the trial flags you want to use. Here we've selected that the
    // trial data should be stored system-wide (TA_SYSTEM) and that we should
    // use un-resetable verified trials (TA_VERIFIED_TRIAL).
    uint32_t trialFlags = TA_VERIFIED_TRIAL | TA_SYSTEM;

    /* Used to store TurboActivate responses. */
    HRESULT         hr;
    GENUINE_OPTIONS opts = {0};
    opts.nLength         = sizeof(GENUINE_OPTIONS);

    // In this example we won't show an error if the activation
    // was done offline by passing the TA_SKIP_OFFLINE flag
    opts.flags = TA_SKIP_OFFLINE;

    // How often to verify with the LimeLM servers (90 days)
    opts.nDaysBetweenChecks = 90;

    // The grace period if TurboActivate couldn't connect to the servers.
    // after the grace period is over TA_IsGenuineEx() will return TA_FAIL instead of
    // TA_E_INET or TA_E_INET_DELAYED
    opts.nGraceDaysOnInetErr = 14;


    /* Get the handle that will be used for TurboActivate function calls.

       TODO: paste your Version GUID here.
    */
    taHandle = TA_GetHandle(_T("18324776654b3946fc44a5f3.49025204"));

    if (taHandle == 0)
    {
        printf("Failed to get the handle for the Version GUID specified. ");
        printf("Make sure the Version GUID is correct, and that TurboActivate.dat is in the same folder as your app.\n\n");
        printf("Or use TA_PDetsFromPath() to load the TurboActivate.dat first before getting the handle.\n");
        exit(1);
    }

    hr = TA_IsGenuineEx(taHandle, &opts);

    if (hr == TA_OK || hr == TA_E_FEATURES_CHANGED || hr == TA_E_INET || hr == TA_E_INET_DELAYED)
    {
        TCHAR * featureValue;

        printf("YourApp is activated and genuine! Enable any app features now.\n");

        if (hr == TA_E_INET || hr == TA_E_INET_DELAYED)
        {
            // TODO: show a warning to your customers that this time (or the last time)
            // the IsGenuineEx() failed to connect to the LimeLM servers.
            printf("YourApp is activated, but it failed to verify the activation with the LimeLM servers. You can still use the app for the duration of the grace period.\n");
        }

        // If this app is activated then you can get a custom license
        // field value (completely optional)
        // See: https://wyday.com/limelm/help/license-features/
        /*

        // First get the size of the buffer that we need to store the custom license
        // field.
        hr = TA_GetFeatureValue(taHandle, _T("your feature value"), 0, 0);

        // allocate the buffer based on the size TurboActivate told us.
        featureValue = (TCHAR *)malloc(hr * sizeof(TCHAR));

        // try to get the value and store it in the buffer
        hr = TA_GetFeatureValue(taHandle, _T("your feature value"), featureValue, hr);

        if (hr == TA_OK)
        {
#ifdef _WIN32
            wprintf(L"Feature value: %s\n", featureValue);
#else
            printf("Feature value: %s\n", featureValue);
#endif
        }
        else
            printf("Getting feature failed: 0x%x\n", hr);

        free(featureValue);

        */
    }
    else  // not activated or genuine
    {
        uint32_t trialDays = 0;

        // Look in TurboActivate.h for what the error codes mean.
        printf("Not activated: hr = 0x%x\n", hr);

        // Check if the failure was a result of the customer not being activated
        // OR if the failure was a result the customer not being able to re-verify with
        // the activations servers.
        if (TA_IsActivated(taHandle) == TA_OK)
        {
            // There is still activation data on the computer, and it's valid.

            // This means that IsGenuineEx() is saying "not activated" (a.k.a. TA_FAIL)
            // because the customer blocked connections to the activation servers (intentionally or not)
            // for nDaysBetweenChecks + nGraceDaysOnInetErr days.

            // What you should do now is prompt the user telling them before they can use your app that they need
            // to reverify with the activation servers.

            char userResp = 0;

            printf("You must reverify with the activation servers before you can use this app. ");
            printf("Type R and then press enter to retry after you've ensured that you're connected to the internet. ");
            printf("Or to exit the app press X.\n");

            while ((userResp = getchar()) != 'X' && userResp != 'x')
            {
                if (userResp == 'R' || userResp == 'r')
                {
                    // Now we're using TA_IsGenuine() to retry immediately. Note that we're not using
                    // TA_IsGenuineEx() because TA_IsGenuineEx() waits 5 hours after an internet failure
                    // before retrying to contact the servers. TA_IsGenuine() retries immediately.
                    hr = TA_IsGenuine(taHandle);

                    if (hr == TA_OK || hr == TA_E_FEATURES_CHANGED)
                    {
                        printf("Successfully reverified with the servers! You can now continue to use the app!\n");
                        break;
                    }
                    else
                    {
                        printf("Failed to reverify with the servers. ");
                        printf("Make sure you're connected to the internet and that you're not blocking access to the activation servers. ");
                        printf("Then press R to retry again.: Error code = 0x%x\n", hr);

                        // Note: actually show a human readable error code to the customer!
                        // hr = 0xNN is not a useful error code. Look in TurboActivate.h for a
                        // full list of error codes and what they mean.
                    }
                }
                else
                {
                    printf("Invalid input. Press R to try to reverify with the servers. Press X to exit the app.\n");
                }
            }

            // exit the app
            if (userResp == 'X' || userResp == 'x')
                exit(1);
        }
        else
        {
            // The customer was never activated or deactivated (or got deactivated).
        }

        // Start or re-validate the trial if it has already started.
        // This need to be called at least once before you can use
        // any other trial functions.
        hr = TA_UseTrial(taHandle, trialFlags, NULL);

        if (hr == TA_OK)
        {
            // Get the number of trial days remaining.
            hr = TA_TrialDaysRemaining(taHandle, trialFlags, &trialDays);

            if (hr == TA_OK)
            {
                printf("Trial days remaining: %d\n", trialDays);

                if (trialDays > 0)
                {
                    // Set the function that TurboActivate will call from another thread
                    // letting your app know of trial expiration (either naturally, or
                    // because of customer fraud).
                    hr = TA_SetTrialCallback(taHandle, trialCallback, NULL);

                    if (hr != TA_OK)
                        printf("Error setting trial callback: hr = 0x%x\n", hr);

                    // Wait around for user-input
                    // you can remove this in a real app, because your
                    // real app will be doing things.
                    printf("\nPress <Enter> to exit...\n");
                    getchar();
                    exit(0);
                }
            }
            else
                printf("Failed to get the trial days remaining: hr = 0x%x\n", hr);
        }
        else
            printf("TA_UseTrial failed: hr = 0x%x\n", hr);


        //TODO: prompt for a product key (if it's not present)
        //Note: here we're just hard-coding the product key to show how you
        //      save the product key and try to activation

        // Also note we're using the TA_SYSTEM flag. This means the activation will be system-wide.
        // However calling using the TA_SYSTEM flag (the first time only) requires system-admin privileges.
        // If your app will never have system admin privileges then you can use the TA_USER flag.
        hr = TA_CheckAndSavePKey(taHandle, _T("U9MM-4NJ5-QFG8-TWM5-QM75-92YI-NETA"), TA_SYSTEM);
        if (hr == TA_OK)
        {
            printf("Product key saved successfully.\n");

            // try to activate
            hr = TA_Activate(taHandle, NULL);

            if (hr == TA_OK)
                printf("Activated successfully\n");
            else
                printf("Activation failed: hr = 0x%x\n", hr);
        }
        else
            printf("Product key failed to save: hr = 0x%x\n", hr);
    }

    printf("Hello world.\n");
    return 0;
}
