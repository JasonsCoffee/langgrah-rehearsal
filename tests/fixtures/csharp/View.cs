using UnityEngine;
namespace Game
{
    public class View : MonoBehaviour
    {
        [SerializeField] private int score;
        public void SetScore(int value) { score = value; }
        public void ReorderQueue(int from, int to) { }
    }
}
