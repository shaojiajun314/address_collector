import platform
import asyncio
import aiohttp
import argparse
from json import dumps
from random import randint
from threading import Thread
from eth_account import Account

SLEEP_SECONDS = 10

class Gather():
	def __init__(self, rpcs, async_nums, thread_nums=None):
		self.async_nums = async_nums
		self.rpcs = rpcs
		self.rpcs_length = len(self.rpcs)
		if not thread_nums:
			from multiprocessing import cpu_count 
			self.thread_nums = cpu_count()
		else:
			self.thread_nums = thread_nums
		# self.descriptors_limits = descriptors_limits

	def run(self):
		print(f'running.....\r\nthread: {self.thread_nums}, coroutine_nums: {self.async_nums}')
		ts = [
			Thread(target=self.detect)
			for i in range(self.thread_nums)
		]
		for i in ts:
			i.start()
		for i in ts:
			i.join()


	def detect(self):
		plat = platform.system().lower()
		if plat == 'windows':
		    print('windows系统')
		    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
		else:
		    print('linux/mac 系统')
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		# descriptors_limits_semaphore = asyncio.Semaphore(self.descriptors_limits // self.thread_nums)
		loop.run_until_complete(asyncio.gather(
			*[
				asyncio.ensure_future(self.__generate_key_task(), loop=loop)
				for i in range(self.async_nums)
			]
		))
		return

	@property
	def rpc(self):
		return self.rpcs[randint(0, self.rpcs_length-1)] 

	async def __generate_key_task(self):
		timeout = aiohttp.ClientTimeout(total=2)
		count = 1
		while 1:
			acct = Account.create()
			try:
				async with aiohttp.ClientSession(timeout=timeout) as session:
					r = await session.post(
						self.rpc,
						json={
							'method': 'eth_getBalance',
							'params': (acct.address, 'latest')
						}
					)
					if r.status != 200:
						if r.status != 429:
							print(f'error status {r.status}')
						await asyncio.sleep(SLEEP_SECONDS)
						continue
					
					j = await r.json()
					if j['result'] != '0x0':
						f = open(acct.address, 'w')
						f.write(dumps({
							'key': acct.key.hex()	
						}))
						f.close()
					# print(j)
					if count == 10:
						print('got 10')
					if count == 1000000:
						print('got 1000000')
						count = 0
					count += 1
			except asyncio.exceptions.TimeoutError:
				continue
			except:
				exit(1)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='参数说明')
	parser.add_argument('--coroutine_nums', type=int, required=True, help='协程数量')
	parser.add_argument('--thread_nums', type=int, default=0, help='线程数量')
	parser.add_argument('--rpcs', type=str, required=True, help='rpc 地址","分割')
	# parser.add_argument('--descriptors_limits', type=int, required=True, help='句柄数量限制')
	args = parser.parse_args()
	rpcs = args.rpcs.split(',')
	g = Gather(
		rpcs=rpcs,
		async_nums=args.coroutine_nums or 10,
		thread_nums=args.thread_nums,
		# descriptors_limits=args.descriptors_limits
	)
	g.run()
