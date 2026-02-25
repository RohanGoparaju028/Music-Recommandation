using Microsoft.AspNetCore.Mvc;
using Backend.Services;

namespace Backend.Controllers;

[ApiController]
[Route("[controller]")]
public class MusicController : ControllerBase
{
    private readonly EmotionalSerivces _emotionService;
    private readonly SpotifyService _spotifyService;

    public MusicController(
        EmotionalSerivces emotionService,
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

        var result = await _spotifyService.PlayMusicBasedOnEmotion(emotion);

        return Ok(new
        {
            detectedEmotion = emotion,
            message = result
        });
    }
}
