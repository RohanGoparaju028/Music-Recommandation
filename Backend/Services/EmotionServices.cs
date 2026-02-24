using System.Net.Http;
using System.Text.Json;
namespace Backend.Services;
public class EmotionalSerivces 
{
     public async Task<string>  GetEmotion() 
     {
        HttpClient client = new();
        var response = await client.PostAsync("http://127.0.0.1:8000/emotion",null)
        if(response.IsSuccessStatusCode) 
        {
            var json = await responese.Content.ReadAsStringAsync();
            var data = JsonSerializer.Deserialize<EmotionalResponse>(json)
            retrurn data.dominantemotion;
        }
        return "Cannot access the server";
     }
}