using Backend.Services;
var builder = WebApplication.CreateBuilder(args);
builder.Services.AddHttpClient<EmotionalSerivces >();
builder.Services.AddScoped<SpotifyService>();
builder.Services.AddControllers();
builder.Services.AddOpenApi();
builder.Services.AddCors(options => {
    options.AddPolicy("AllowReactApp",
        policy => policy.WithOrigins("http://localhost:5173") // Vite default port
                        .AllowAnyMethod()
                        .AllowAnyHeader());
});
var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}
app.UseCors("AllowReactApp");
app.UseHttpsRedirection();

app.MapControllers();
app.Run();


