using Backend.Models;
using System.Text.Json;
namespace Backend.Services;
public class EmotionalSerivces 
    {
        private readonly HttpClient _httpClient;

        public EmotionalSerivces(HttpClient httpClient)
        {
            _httpClient = httpClient;
        }

        public async Task<string> GetEmotion() 
        {
            var content = new StringContent("{}", System.Text.Encoding.UTF8, "application/json");
            var response = await _httpClient.PostAsync("http://127.0.0.1:8000/emotion", content);
            
            if (response.IsSuccessStatusCode) 
            {
                var json = await response.Content.ReadAsStringAsync();
                var data = JsonSerializer.Deserialize<EmotionalResponse>(json);
                return data.DominantEmotion;
            }
            return "Cannot access the server";
        }
    }
