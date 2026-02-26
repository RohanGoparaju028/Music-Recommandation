using Backend.Services;
var builder = WebApplication.CreateBuilder(args);
builder.Services.AddHttpClient<EmotionalSerivces >();
builder.Services.AddScoped<SpotifyService>();
builder.Services.AddControllers();
builder.Services.AddOpenApi();
var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseHttpsRedirection();

app.MapControllers();

app.Run();


