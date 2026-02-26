using SpotifyAPI.Web;
using System.Threading.Tasks;

namespace Backend.Services
{
    public class SpotifyService
    {
        private readonly string _clientId = ""; 
        private readonly string _clientSecret = ""; 
        private static readonly Random _random = new Random();  

       public async Task<string?> GetSpotifyTrackUrl(string emotion)
      {
         var keyword = MapEmotionToKeyword(emotion);

        var config = SpotifyClientConfig.CreateDefault();
        var request = new ClientCredentialsRequest(_clientId, _clientSecret);
        var response = await new OAuthClient(config).RequestToken(request);
        var spotify = new SpotifyClient(config.WithToken(response.AccessToken));

        var searchRequest = new SearchRequest(SearchRequest.Types.Track, keyword);
        var searchResponse = await spotify.Search.Item(searchRequest);

        if (searchResponse.Tracks.Items?.Count > 0)
        {
           var randomTrack = searchResponse.Tracks.Items[_random.Next(searchResponse.Tracks.Items.Count)];
            return randomTrack.ExternalUrls["spotify"];
         }

        return null;
        }

        private string MapEmotionToKeyword(string emotion)
        {
            return emotion.ToLower() switch
            {
                "happy" => "happy upbeat",
                "sad" => "sad mellow",
                "neutral" => "calm",
                "surprised" => "intense",
                "angry" => "angry",
                _ => "pop"
            };
        }
    }
}