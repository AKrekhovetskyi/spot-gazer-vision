import asyncio

from src import SpotGazer


class TestSpotGazer:
    def test_start_stop_detection(self) -> None:
        parking_lots_example = [
            [
                {
                    "parking_lot_id": 1,
                    # TODO @AKrekhovetskyi: Use `ultralytics.data.loaders.get_best_youtube_url` with the  # noqa: FIX002
                    # `method="yt-dlp"` argument to get working YouTube stream links.
                    # Original link: https://www.youtube.com/watch?v=LcSaBafrb-w&ab_channel=LingoNetworks
                    # https://github.com/AKrekhovetskyi/spot-gazer-vision/issues/5
                    "stream_source": "https://manifest.googlevideo.com/api/manifest/hls_playlist/expire/1752003212/ei/LB5taL3tA7zs6dsPn5PRMQ/ip/91.221.218.10/id/LcSaBafrb-w.3/itag/270/source/yt_live_broadcast/requiressl/yes/ratebypass/yes/live/1/sgovp/gir%3Dyes%3Bitag%3D137/rqh/1/hls_chunk_host/rr2---sn-voxpm-3c2e.googlevideo.com/xpc/EgVo2aDSNQ%3D%3D/playlist_duration/30/manifest_duration/30/bui/AY1jyLOZs7rg5y-d8QseczhCQyae6kczSuRgCQKFh1APzVznDc0emSPSh8f12UO4XBUv8-TFhr4tcVOq/spc/l3OVKXwwuNAgxoynVStcKAc0HApHNvQ8Sz_GwEXDVwywoKriqssvihzbvdJvCw/vprv/1/playlist_type/DVR/initcwndbps/2112500/met/1751981612,/mh/Jc/mm/44/mn/sn-voxpm-3c2e/ms/lva/mv/m/mvi/2/pl/24/rms/lva,lva/dover/13/pacing/0/short_key/1/keepalive/yes/mt/1751981085/sparams/expire,ei,ip,id,itag,source,requiressl,ratebypass,live,sgovp,rqh,xpc,playlist_duration,manifest_duration,bui,spc,vprv,playlist_type/sig/AJfQdSswRQIhAIhmqc3KqJV1nKEslbzxxhvcyamAi2NWCTV7UB2DDfKOAiALPHJ9r2680o7VzkE0mUMP4C-zfZZOaZPctcWovruxow%3D%3D/lsparams/hls_chunk_host,initcwndbps,met,mh,mm,mn,ms,mv,mvi,pl,rms/lsig/APaTxxMwRQIgNt3q1PjGLFAD1JkN4Y5m5Z0q_Il300VT9VGBA2k-F8kCIQDhLII9nGV2xF69CIJ2tWcyCZqE7Cq6u-bbZlmUWxOJ-A%3D%3D/playlist/index.m3u8",  # codespell:ignore  # noqa: E501
                    "processing_rate": 5,
                }
            ],
        ]

        spot_gazer = SpotGazer(parking_lots=parking_lots_example)
        try:
            asyncio.run(asyncio.wait_for(spot_gazer.start_detection(), 10))
        except (KeyboardInterrupt, TimeoutError):
            spot_gazer.stop_detection()
