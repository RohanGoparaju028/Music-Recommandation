using System.Text.Json.Serialization;

namespace Backend.Models;

public class EmotionalResponse
{
    [JsonPropertyName("status")]
    public string Status {get;set;}
    [JsonPropertyName("dominantEmotion")]
    public string DominantEmotion {get;set;}
}
