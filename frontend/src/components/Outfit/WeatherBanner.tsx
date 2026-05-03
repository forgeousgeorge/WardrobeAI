interface WeatherSnapshot {
  temp_c: number
  feels_like_c: number
  temp_f: number
  feels_like_f: number
  description: string
  icon_code: string
  humidity: number
  wind_kph: number
  wind_mph: number
}

interface Props {
  weather: WeatherSnapshot
}

export default function WeatherBanner({ weather }: Props) {
  const iconUrl = `https://openweathermap.org/img/wn/${weather.icon_code}@2x.png`
  const tempF = weather.temp_f ?? Math.round(weather.temp_c * 9 / 5) + 32
  const feelsF = weather.feels_like_f ?? Math.round(weather.feels_like_c * 9 / 5) + 32
  const windMph = weather.wind_mph ?? Math.round(weather.wind_kph / 1.609)

  return (
    <div className="mx-4 mt-4 rounded-2xl bg-gradient-to-r from-brand-500 to-brand-700 p-4 text-white shadow-md">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-3xl font-bold">{Math.round(tempF)}°F</p>
          <p className="text-sm opacity-90 capitalize">{weather.description}</p>
          <p className="text-xs opacity-75 mt-1">
            Feels like {Math.round(feelsF)}°F · {windMph} mph wind
          </p>
        </div>
        <img src={iconUrl} alt={weather.description} className="w-16 h-16" />
      </div>
    </div>
  )
}
