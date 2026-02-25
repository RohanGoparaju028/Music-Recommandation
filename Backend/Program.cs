var builder = WebApplication.CreateBuilder(args);
builder.Services.AddHttpClient<EmotionalSerivces>();
builder.Services.AddOpenApi();
var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseHttpsRedirection();


app.Run();


