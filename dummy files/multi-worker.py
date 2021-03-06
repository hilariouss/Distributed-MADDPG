import tensorflow as tf
import threading, queue
import gym

N_WORKER = 4

EP_MAX = 100
EP_LEN = 50

class Brain(object):
	def __init__(self):
		pass

	def update(self):
		global GLOBAL_UPDATE_COUNTER

		while not COORD.should_stop():
			if GLOBAL_EP < EP_MAX:
				# print("I am brain")
				UPDATE_EVENT.wait()
				print("update global brain")
				UPDATE_EVENT.clear()
				GLOBAL_UPDATE_COUNTER = 0
				ROLLING_EVENT.set()
				pass

class Worker(object):
	def __init__(self, wid):
		self.wid = wid
		self.env = gym.make("CartPole-v0")

	def work(self):
		print("worker{:d} started".format(self.wid))
		global GLOBAL_EP, GLOBAL_UPDATE_COUNTER

		while not COORD.should_stop():
			s = self.env.reset()
			for stp in range(EP_LEN):
				if not ROLLING_EVENT.is_set():    # while global PPO is updating
                    ROLLING_EVENT.wait() 
				print(self.wid, "rendering")
				self.env.render()
				s2, _, done, _ = self.env.step(self.env.action_space.sample())
				s = s2

				GLOBAL_UPDATE_COUNTER += 1
				if stp == EP_LEN - 1 or GLOBAL_UPDATE_COUNTER >= 64:
					
					if GLOBAL_UPDATE_COUNTER >= 64: # minbatch size
						ROLLING_EVENT.clear()
						UPDATE_EVENT.set()

					if GLOBAL_EP >= EP_MAX:
						COORD.request_stop()
						break
			GLOBAL_EP += 1


if __name__ == "__main__":

	UPDATE_EVENT, ROLLING_EVENT = threading.Event(), threading.Event()
	UPDATE_EVENT.clear()
	ROLLING_EVENT.set()

	GLOBAL_UPDATE_COUNTER, GLOBAL_EP = 0, 0

	GLOBAL_EP = 0

	global_brain = Brain()

	workers = [Worker(wid=i) for i in range(N_WORKER)]

	threads = []

	COORD = tf.train.Coordinator()

	QUEUE = queue.Queue()

	for worker in workers:
		t = threading.Thread(target=worker.work, args=())
		t.start()
		threads.append(t)

	threads.append(threading.Thread(target=global_brain.update, args=()))

	print("Active thread number:", threading.active_count())
	
	threads[-1].start()

	COORD.join(threads)


	##	s = env.reset()



