using Microsoft.AspNetCore.Mvc;
using SpotifyAPI.Web;
using Backend.Services;

namespace Backend.Controllers;

[ApiController]
[Route("[controller]")]
public class MusicController : ControllerBase
{
    private readonly EmotionalSerivces  _emotionService;
    private readonly SpotifyService _spotifyService;

    public MusicController(
       EmotionalSerivces  emotionService,
        SpotifyService spotifyService)
    {
        _emotionService = emotionService;
        _spotifyService = spotifyService;
    }
    [HttpGet("play")]
    public async Task<IActionResult> PlayMusic()
    {
    var emotion = await _emotionService.GetEmotion();

    if (emotion == "Cannot access the server")
        return BadRequest("Emotion service unavailable");
    var trackUrl = await _spotifyService.GetSpotifyTrackUrl(emotion);

    if (string.IsNullOrEmpty(trackUrl))
    {
        return NotFound("No tracks found for this emotion.");
    }

    // This command tells the browser to go to the Spotify page immediately
    return Redirect(trackUrl);
}
}
