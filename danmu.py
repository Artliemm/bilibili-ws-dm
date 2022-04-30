import json
import zlib
import brotli
import asyncio
import binascii
import websockets

class bilibiliDM:

    def __init__(self, roomid,remote):
        self.HeartBeat = '0000001f0010000100000002000000015b6f626a656374204f626a6563745d' # b'[object Object]'
        self.data_raw = '000000{headerLen}001000010000000700000001{raw}'
        self.remote = remote
        self.info={
            "uid":0,
            "roomid":roomid,
            "protover":3,
            "platform":"web",
            "type":2
        }
        self.JsonToHex()                  

    async def start(self):
        async with websockets.connect(self.remote) as ws:
            await ws.send(bytes.fromhex(self.data_raw)) #发送连接数据
            tasks = [self.recvDM(ws), self.sendHeartBeat(ws)]
            await asyncio.wait(tasks)

    async def sendHeartBeat(self, websocket):
        while True:
            await asyncio.sleep(30)
            await websocket.send(bytes.fromhex(self.HeartBeat))
            print('\033[0;33m[HeartBeat]\033[0m')
    
    async def recvDM(self, websocket):
        while True:
            recv_text = await websocket.recv()
            self.parseDM(recv_text)

    def JsonToHex(self):
        data=json.dumps(self.info).replace(' ','').encode()
        headerLen=hex(16+len(data))[2:]
        raw=binascii.hexlify(data).decode()
        self.data_raw=self.data_raw.format(headerLen=headerLen,raw=raw) 

    def parseDM(self, data):
        # 获取数据包的长度，版本和操作类型
        packetLen = int(data[:4].hex(), 16)
        ver = int(data[6:8].hex(), 16)
        op = int(data[8:12].hex(), 16)

        # 有的时候可能会多个数据包连在一起发过来，所以利用前面的数据包长度判断
        if (len(data) > packetLen):
            self.parseDM(data[packetLen:])
            data = data[:packetLen]

        # brotli 压缩数据包
        if (ver == 3):
            data = brotli.decompress(data[16:])
            self.parseDM(data)
            return

        # zlib 压缩数据包
        if (ver == 2):
            data = zlib.decompress(data[16:])
            self.parseDM(data)
            return

        # ver 为1的时候为进入房间后或心跳包服务器的回应。op 为3的时候为房间的人气值
        if(ver == 1):
            if(op == 3):
                print('\033[0;33m[RENQI]  {}\033[0m'.format(int(data[16:].hex(),16)))
            return

        # op 为5意味着这是通知消息，cmd 基本就那几个了
        if (op == 5):
            try:
                jd = json.loads(data[16:].decode('utf-8', errors='ignore'))
                if (jd['cmd'] == 'DANMU_MSG'):
                    print('\033[0;32m[弹 幕] ', jd['info'][2][1], ': ', jd['info'][1], '\033[0m')
                elif(jd['cmd']=='SEND_GIFT'):
                    print('\033[0;33m[GITT] ',jd['data']['uname'], jd['data']['action'], jd['data']['num'], 'x', jd['data']['giftName'])
                elif(jd['cmd']=='LIVE'):
                    print('\033[0;33m直播开始!\033[0m')
                elif(jd['cmd']=='PREPARING'):
                    print('\033[0;33m直播结束!\033[0m')
                else:
                    print('\033[0;33m[OTHER] ', jd['cmd'],'\033[0m')
            except Exception as e:
                pass

    def run(self):
        asyncio.run(self.start())

if __name__=='__main__':
    roomid = 22909669
    remote='wss://broadcastlv.chat.bilibili.com/sub'
    try:
        print('\033[0;32m[房间号]',roomid,'\033[0m')
        bilibiliDM(roomid, remote).run()
    except KeyboardInterrupt as exc:
        print('Quit.')



            