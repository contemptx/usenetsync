package main

import (
	"fmt"
	"os"
	"strconv"

	"golang.wyday.com/turboactivate"
)

var isGenuine = false

// Set the trial flags you want to use. Here we've selected that the
// trial data should be stored system-wide (TA_SYSTEM) and that we should
// use un-resetable verified trials (TA_VERIFIED_TRIAL).
var trialFlags = turboactivate.TASystem | turboactivate.TAVerifiedTrial

// Don't use 0 for either of these values.
// We recommend 90, 14. But if you want to lower the values
// we don't recommend going below 7 days for each value.
// Anything lower and you're just punishing legit users.
const daysBetweenChecks = 90
const gracePeriodDays = 14

func main() {

	//TODO: goto the version page at LimeLM and paste this GUID here
	ta, err := turboactivate.NewTurboActivate("18324776654b3946fc44a5f3.49025204", "")

	if err != nil {
		// failed to construct the TurboActivate object
		// bail out now.
		panic(err)
	}

	// Check if we're activated, and every 90 days verify it with the activation servers
	// In this example we won't show an error if the activation was done offline
	// (see the 3rd parameter of the IsGenuineEx() function)
	isGr, err := ta.IsGenuineEx(daysBetweenChecks, gracePeriodDays, true, false)

	if err != nil {
		panic(err)
	}

	if isGr == turboactivate.IGRGenuine ||
		isGr == turboactivate.IGRGenuineFeaturesChanged ||

		// an internet error means the user is activated but
		// TurboActivate failed to contact the LimeLM servers
		isGr == turboactivate.IGRInternetError {

		isGenuine = true
	}

	if !isGenuine {

		// If IsGenuineEx() is telling us we're not activated
		// but the IsActivated() function is telling us that the activation
		// data on the computer is valid (i.e. the crypto-signed-fingerprint matches the computer)
		// then that means that the customer has passed the grace period and they must re-verify
		// with the servers to continue to use your app.

		//Note: DO NOT allow the customer to just continue to use your app indefinitely with absolutely
		//      no reverification with the servers. If you want to do that then don't use IsGenuine() or
		//      IsGenuineEx() at all -- just use IsActivated().
		isAct, err := ta.IsActivated()

		if err != nil {
			panic(err)
		}

		if isAct {
			// We're treating the customer as is if they aren't activated, so they can't use your app.

			// However, we show them a prompt where they can reverify with the servers immediately.

			//TODO: prompt the user however you want
			var userWantsToRetry = true

			for userWantsToRetry {

				// Now we're using TA_IsGenuine() to retry immediately. Note that we're not using
				// TA_IsGenuineEx() because TA_IsGenuineEx() waits 5 hours after an internet failure
				// before retrying to contact the servers. TA_IsGenuine() retries immediately.
				isGr, err := ta.IsGenuine()

				if err != nil {
					panic(err)
				}

				if isGr == turboactivate.IGRGenuine ||
					isGr == turboactivate.IGRGenuineFeaturesChanged {

					fmt.Println("Successfully reverified with the servers! You can now continue to use the app!")
					isGenuine = true

					// no longer need to retry
					userWantsToRetry = false

				} else {

					fmt.Println("Failed to reverify with the servers.")
					fmt.Println("Make sure you're connected to the internet and that you're not blocking access to the activation servers.")

					//TODO: prompt the user again

					userWantsToRetry = false
				}
			}
		}
	}

	// If this app is activated then you can get custom license fields.
	// See: https://wyday.com/limelm/help/license-features/
	if isGenuine {

		updateExpires, err := ta.GetFeatureValue("update_expires")

		if err != nil {
			fmt.Println("The custom license field doesn't exist. (or some other error).")
		} else {
			fmt.Println("Update expires: " + updateExpires)
		}

	} else {

		// trial days is 0 by default
		var trialDaysRemain uint32

		// begin or re-verify the trial
		trialNotExpired, err := ta.UseTrial(trialFlags, "")

		if err != nil {
			panic(err)
		}

		if trialNotExpired {

			// get the number of remaining trial days
			trialDaysRemain, err = ta.TrialDaysRemaining(trialFlags)

			if err != nil {
				panic(err)
			}
		}

		if trialDaysRemain == 0 {
			// no more trial days, just exit the app
			fmt.Println("There are no more trial days. Exiting the app immediately.")
			os.Exit(1)
		} else {
			fmt.Println("Your trial expires in " + strconv.FormatUint(uint64(trialDaysRemain), 10) + " days.")
		}
	}

	// Here's where your program would actually begin.
	fmt.Println("Hello world!")
}
