using UnityEngine;
using UnityEngine.UI;

namespace FrameworkVisualDemo
{
    // Architect-prepared bindings. This is a presentation preview, not game logic.
    public sealed class ExpeditionPreviewShell : MonoBehaviour
    {
        public Button confirmButton;
        public Button resetButton;
        public Text statusText;
        public Image heroImage;

        public void PreviewReady()
        {
            statusText.text = "READY FOR REVIEW";
            statusText.color = new Color32(166, 231, 199, 255);
        }

        public void ResetPreview()
        {
            statusText.text = "BASELINE PREVIEW";
            statusText.color = new Color32(246, 169, 139, 255);
        }
    }
}
