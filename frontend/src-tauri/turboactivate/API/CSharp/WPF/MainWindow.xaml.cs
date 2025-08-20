using System;
using System.Diagnostics;
using System.Windows;
using wyDay.TurboActivate;

namespace CSharp_WPF
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        readonly TurboActivate ta;
        bool isGenuine;

        // Set the trial flags you want to use. Here we've selected that the
        // trial data should be stored system-wide (TA_SYSTEM) and that we should
        // use un-resetable verified trials (TA_VERIFIED_TRIAL).
        readonly TA_Flags trialFlags = TA_Flags.TA_SYSTEM | TA_Flags.TA_VERIFIED_TRIAL;

        // Don't use 0 for either of these values.
        // We recommend 90, 14. But if you want to lower the values
        // we don't recommend going below 7 days for each value.
        // Anything lower and you're just punishing legit users.
        const uint DaysBetweenChecks = 90;
        const uint GracePeriodLength = 14;

        public MainWindow()
        {
            InitializeComponent();

            try
            {
                //TODO: goto the version page at LimeLM and paste this GUID here
                ta = new TurboActivate("18324776654b3946fc44a5f3.49025204");

                // set the trial changed handler
                ta.TrialChange += TurboActivate_TrialChange;

                // Check if we're activated, and every 90 days verify it with the activation servers
                // In this example we won't show an error if the activation was done offline
                // (see the 3rd parameter of the IsGenuine() function)
                // https://wyday.com/limelm/help/offline-activation/
                IsGenuineResult gr = ta.IsGenuine(DaysBetweenChecks, GracePeriodLength, true);

                isGenuine = gr == IsGenuineResult.Genuine ||
                            gr == IsGenuineResult.GenuineFeaturesChanged ||

                            // an internet error means the user is activated but
                            // TurboActivate failed to contact the LimeLM servers
                            gr == IsGenuineResult.InternetError;


                // If IsGenuineEx() is telling us we're not activated
                // but the IsActivated() function is telling us that the activation
                // data on the computer is valid (i.e. the crypto-signed-fingerprint matches the computer)
                // then that means that the customer has passed the grace period and they must re-verify
                // with the servers to continue to use your app.

                //Note: DO NOT allow the customer to just continue to use your app indefinitely with absolutely
                //      no reverification with the servers. If you want to do that then don't use IsGenuine() or
                //      IsGenuineEx() at all -- just use IsActivated().
                if (!isGenuine && ta.IsActivated())
                {
                    // We're treating the customer as is if they aren't activated, so they can't use your app.

                    // However, we show them a dialog where they can reverify with the servers immediately.

                    ReVerifyNow frmReverify = new ReVerifyNow(ta, DaysBetweenChecks, GracePeriodLength) { Owner = this };
                    frmReverify.ShowDialog();

                    if (frmReverify.DialogResult.HasValue && frmReverify.DialogResult.Value)
                    {
                        isGenuine = true;
                    }
                    else if (!frmReverify.noLongerActivated) // the user clicked cancel and the user is still activated
                    {
                        // Just bail out of your app
                        Environment.Exit(1);
                        return;
                    }
                }
            }
            catch (TurboActivateException ex)
            {
                // failed to check if activated, meaning the customer screwed
                // something up so kill the app immediately
                MessageBox.Show("Failed to check if activated: " + ex.Message);
                Environment.Exit(1);
                return;
            }

            ShowTrial(!isGenuine);

            // If this app is activated then you can get custom license fields.
            // See: https://wyday.com/limelm/help/license-features/
            /*
            if (isGenuine)
            {
                string featureValue = ta.GetFeatureValue("your feature name");

                //TODO: do something with the featureValue
            }
            */
        }

        private void mnuActDeact_Click(object sender, RoutedEventArgs e)
        {
            if (isGenuine)
            {
                // deactivate product without deleting the product key
                // allows the user to easily reactivate
                try
                {
                    ta.Deactivate(false);
                }
                catch (TurboActivateException ex)
                {
                    MessageBox.Show("Failed to deactivate: " + ex.Message);
                    return;
                }

                isGenuine = false;
                ShowTrial(true);
            }
            else
            {
                // Note: you can launch the TurboActivate wizard
                //       or you can create you own interface

                // launch TurboActivate.exe to get the product key from
                // the user, and activate.
                Process TAProcess = new Process
                {
                    StartInfo =
                    {
                        FileName = System.IO.Path.Combine(
                            System.IO.Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location),
                                "TurboActivate.exe"
                            )
                    },
                    EnableRaisingEvents = true
                };

                TAProcess.Exited += p_Exited;
                TAProcess.Start();
            }
        }

        /// <summary>This event handler is called when TurboActivate.exe closes.</summary>
        void p_Exited(object sender, EventArgs e)
        {
            // remove the event
            ((Process)sender).Exited -= p_Exited;

            // the UI thread is running asynchronous to TurboActivate closing
            // that's why we can't call CheckIfActivated(); directly
            this.Dispatcher.Invoke(new IsActivatedDelegate(CheckIfActivated));
        }

        delegate void IsActivatedDelegate();

        /// <summary>Rechecks if we're activated -- if so enable the app features.</summary>
        void CheckIfActivated()
        {
            bool isNowActivated = false;

            try
            {
                isNowActivated = ta.IsActivated();
            }
            catch (TurboActivateException ex)
            {
                MessageBox.Show("Failed to check if activated: " + ex.Message);
                return;
            }

            // recheck if activated
            if (isNowActivated)
            {
                isGenuine = true;
                ReEnableAppFeatures();
                ShowTrial(false);
            }
        }

        /// <summary>Put this app in either trial mode or "full mode"</summary>
        /// <param name="show">If true show the trial, otherwise hide the trial.</param>
        void ShowTrial(bool show)
        {
            lblTrialMessage.Visibility = show ? Visibility.Visible : Visibility.Hidden;
            btnExtendTrial.Visibility = show ? Visibility.Visible : Visibility.Hidden;

            mnuActDeact.Header = show ? "Activate..." : "Deactivate";

            if (show)
            {
                uint trialDaysRemaining = 0;

                try
                {
                    ta.UseTrial(trialFlags);

                    // get the number of remaining trial days
                    trialDaysRemaining = ta.TrialDaysRemaining(trialFlags);
                }
                catch (TrialExpiredException)
                {
                    // do nothing because trialDaysRemaining is already set to 0
                }
                catch (TurboActivateException ex)
                {
                    MessageBox.Show("Failed to start the trial: " + ex.Message);
                }

                // if no more trial days then disable all app features
                if (trialDaysRemaining == 0)
                    DisableAppFeatures(false);
                else
                    lblTrialMessage.Content = "Your trial expires in " + trialDaysRemaining + " days.";
            }
        }


        /// <summary>Change this function to disable the features of your app.</summary>
        /// <param name="timeFraudFlag">true if the trial has expired due to date/time fraud.</param>
        void DisableAppFeatures(bool timeFraudFlag)
        {
            //TODO: disable all the features of the program
            txtMain.IsEnabled = false;

            if (!timeFraudFlag)
                lblTrialMessage.Content = "The trial has expired. Get an extension at Example.com";
            else
                lblTrialMessage.Content = "The trial has expired due to date/time fraud detected";
        }

        /// <summary>Change this function to re-enable the features of your app.</summary>
        void ReEnableAppFeatures()
        {
            //TODO: re-enable all the features of the program
            txtMain.IsEnabled = true;
        }

        private void btnExtendTrial_Click(object sender, RoutedEventArgs e)
        {
            TrialExtension trialExt = new TrialExtension(ta, trialFlags) { Owner = this };
            trialExt.ShowDialog();
            
            if (trialExt.DialogResult.HasValue && trialExt.DialogResult.Value)
            {
                // get the number of remaining trial days
                uint trialDaysRemaining = 0;

                try
                {
                    trialDaysRemaining = ta.TrialDaysRemaining(trialFlags);
                }
                catch (TurboActivateException ex)
                {
                    MessageBox.Show("Failed to get the trial days remaining: " + ex.Message);
                }

                // if more trial days then re-enable all app features
                if (trialDaysRemaining > 0)
                {
                    ReEnableAppFeatures();
                    lblTrialMessage.Content = "Your trial expires in " + trialDaysRemaining + " days.";
                }
            }
        }

        void TurboActivate_TrialChange(object sender, StatusArgs e)
        {
            // disable the features of your app
            DisableAppFeatures(e.Status == TA_TrialStatus.TA_CB_EXPIRED_FRAUD);
        }
    }
}
