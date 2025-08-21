'use strict';

var TurboActivate = require('./turboactivate.js');

//TODO: goto the version page at LimeLM and paste this GUID here
var ta = new TurboActivate("18324776654b3946fc44a5f3.49025204");

function BeginYourApp(inTrial = false, trialDays = 0)
{
    console.log("Hello world! Here's where your app code would begin.");
}

function HardFailure(context, errCode)
{
    console.log(context + ": " + errCode);
    process.exit(1);
}

function PromptUserToReverify()
{
    console.log("TODO: before letting the customer use your app, prompt the user to retry verifying with the servers before continuing");

    var userResp = 'n';

    //TODO: prompt the user y/n to reverify immediately. If no is chosen, exit immediately.

    if (userResp === 'n')
    {
        process.exit(1);
    }
    else // "y"
    {
        ta.IsGenuine()
            .then((retObj) => {

                if (retObj === TA_E_INET)
                {
                    // call this function again
                    PromptUserToReverify();
                    return null;
                }
                else if (retObj === TA_OK
                    || retObj === TA_E_FEATURES_CHANGED)
                {
                    // if activated, begin the app immediately
                    BeginYourApp();
                    return null;
                }
                else // TA_FAIL, TA_E_REVOKED, TA_E_ACTIVATE, TA_E_IN_VM
                {
                    HardFailure("Not activated.", retObj);
                }
            })
            .catch((retObj) => { // an error somewhere in the processing

                HardFailure("Something failed! " + retObj, 1);
            });
    }
}

/*
 This callback function is called by the TurboActivate object
 when the trial has expired or the customer is trying to
 fraudulently add more time.
 */
function TATrialChange(status)
{
    //TODO: implement
    switch (status)
    {
        case TA_CB_EXPIRED:
        case TA_CB_EXPIRED_FRAUD:
        default:
            // just call the trial expired function defined below
            // so as to not recreate the same functionality used
            // elsewhere.
            TrialExpired();
            break;
    }
}

function TrialExpired()
{
    //TODO: make this handle trial expiration more gracefully.
    //      just bailing out is a mistake. Instead prompt for a
    //      product key or a trial extension.

    console.log("The trial has expired. TODO: prompt for a product key or trial extension");
    process.exit(1);
}

function PromptForProductKey()
{
    var userEnteredPkey;

    //TODO: prompt the user for the product key

    // validate and save the product key if it's valid
    ta.CheckAndSavePKey(userEnteredPkey, TA_USER)
        .then((retObj) => {

            // the product key was valid and saved successfully
            if (retObj === TA_OK)
                return ta.Activate();
            else // TA_FAIL
            {
                HardFailure("Something failed! " + retObj, 1);
                return null;
            }
        })
        .then((retObj) => { // result from Activate()

            // if null, fall through
            if (retObj === null)
                return null;

            if (retObj === TA_OK)
            {
                // the customer activated successfully, begin your app
                BeginYourApp();
            }
            else
            {
                HardFailure("Activation failed.", retObj);
            }
        })
        .catch((retObj) => { // an error somewhere in the processing

            HardFailure("Something failed! " + retObj, 1);
        });
}


// Set the trial flags you want to use. Here we've selected that
// the trial data should be stored user-wide (TA_USER) and that we
// should use un-resetable verified trials (TA_VERIFIED_TRIAL).
const trialFlags = TA_USER | TA_VERIFIED_TRIAL;

// Don't use 0 for either of these values.
// We recommend 90, 14. But if you want to lower the values
// we don't recommend going below 7 days for each value.
// Anything lower and you're just punishing legit users.
const DaysBetweenChecks = 90;
const GracePeriodLength = 14;

/*
var update_expires = null;

ta.GetFeatureValue("update_expires")
    .then((retObj) => {

        // Save the expiration date so we can use it elsewhere
        update_expires = retObj[1];

        // if the custom license field exists, then
        // check if it has expired.
        if (retObj[0] === TA_OK)
            return ta.IsDateValid(retObj[1]);
        else
            return TA_FAIL;
    })
    .then((retObj) => {

        // if null, fall through
        if (retObj === null)
            return null;

        if (retObj === TA_OK)
        {
            BeginYourApp();
            return null;
        }
        else
        {
            //TODO: instead of just throwing a hard error
            // give your customer a chance to buy more from you!
            HardFailure("Subscription expired!", retObj);
            return null;
        }
    });
*/



ta.IsGenuineEx(DaysBetweenChecks, GracePeriodLength, true)
    .then((retObj) => {

        // if activated, begin the app immediately
        if (retObj === TA_OK
            || retObj === TA_E_FEATURES_CHANGED
            || retObj === TA_E_INET
            || retObj === TA_E_INET_DELAYED)
        {
            BeginYourApp();
            return null;
        }
        else // TA_FAIL
            return ta.IsActivated();
    })
    .then((retObj) => { // result from IsActivated()

        // if null, fall through
        if (retObj === null)
            return null;

        if (retObj === TA_OK)
        {
            // If IsGenuineEx() is telling us we're not activated
            // but the IsActivated() function is telling us that the
            // activation data on the computer is valid (i.e. the
            // crypto-signed-fingerprint matches the computer) then
            // that means that the customer has passed the grace
            // period and they must re-verify with the servers to
            // continue to use your app.

            //Note: DO NOT allow the customer to just continue to use
            // your app indefinitely with absolutely no reverification
            // with the servers. If you want to do that then don't use
            // IsGenuine() or IsGenuineEx() at all -- just
            // use IsActivated().
            PromptUserToReverify();
            return null;
        }
        else // TA_FAIL (not activated, start the trial)
        {
            // Start / re-verify the trial, provide a function
            // to be called asynchronously when the trial expires
            // and pass in the type of trial (see trialFlags).

            // You still need to call TrialDaysRemaining() to
            // see the trial days remaining (because the callback is
            // *not*) called if the trial has already expired outside
            // the life of this program.
            return ta.UseTrial(TATrialChange, trialFlags);
        }
    })
    .then((retObj) => { // result from UseTrial()

        // if null, fall through
        if (retObj === null)
            return null;

        if (retObj === TA_OK)
            return ta.TrialDaysRemaining(trialFlags);
        else if (retObj === TA_E_TRIAL_EXPIRED)
        {
            TrialExpired();
            return null;
        }
        else
            HardFailure("Failed to start the trial", retObj);
    })
    .then((retObj) => { // result from TrialDaysRemaining()

        // if null, fall through
        if (retObj === null)
            return null;

        if (retObj[0] === TA_OK)
        {
            // if the customer is in a trial, being your app
            if (retObj[1] > 0)
                BeginYourApp(true, retObj[1]);
            else // no more trial days remaining
            {
                TrialExpired();
                return null;
            }
        }
        else
        {
            HardFailure("Failed to get the trial days remaining",
                retObj[0]);
        }
    })
    .catch((retObj) => { // an error somewhere in the processing

        HardFailure("Something failed! " + retObj, 1);
    });
