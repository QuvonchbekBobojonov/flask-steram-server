(function () {
  if (window.LiveKitProctor) return

  const s = document.createElement("script")
  s.src = "https://cdn.jsdelivr.net/npm/livekit-client/dist/livekit-client.umd.min.js"
  s.onload = init
  document.head.appendChild(s)

  function init() {
    window.LiveKitProctor = async function (opts = {}) {
      const {
        tokenEndpoint,
        user,
        autoStart = true
      } = opts

      if (!tokenEndpoint) throw new Error("tokenEndpoint required")
      if (!user) throw new Error("user required")

      const USER = user + "_" + Date.now()

      let room = null
      let tracks = []

      async function start() {
        const r = await fetch(`${tokenEndpoint}/${encodeURIComponent(USER)}`)
        const d = await r.json()

        room = new LivekitClient.Room()
        await room.connect(d.url, d.token)

        tracks = await LivekitClient.createLocalTracks({
          video: true,
          audio: false
        })

        await room.localParticipant.publishTrack(tracks[0])
      }

      async function stop() {
        tracks.forEach(t => t.stop())
        tracks = []
        if (room) {
          room.disconnect()
          room = null
        }
      }

      if (autoStart) await start()

      return { start, stop, user: USER }
    }
  }
})()
