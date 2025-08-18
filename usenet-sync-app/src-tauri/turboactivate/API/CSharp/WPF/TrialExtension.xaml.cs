using System;
using System.Windows;

namespace wyDay.TurboActivate
{
    /// <summary>
    /// Interaction logic for TrialExtension.xaml
    /// </summary>
    public partial class TrialExtension : Window
    {
        private readonly TurboActivate ta;
        private readonly TA_Flags trialFlags;

        public TrialExtension(TurboActivate ta, TA_Flags useTrialFlags)
        {
            this.ta = ta;
            this.trialFlags = useTrialFlags;

            InitializeComponent();
        }

        private void btnCancel_Click(object sender, RoutedEventArgs e)
        {
            Close();
        }

        private void btnOK_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // try to extend the trial and close the form
                ta.ExtendTrial(txtExtension.Text, trialFlags);
                DialogResult = true;
                Close();
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message, "Trial extension failed.", MessageBoxButton.OK, MessageBoxImage.Error);
                txtExtension.Focus();
            }
        }
    }
}
