class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			self.file = open(filename, 'rb')
		except:
			raise IOError
		self.frameNum = 0
		
	def nextFrame(self):
		"""Get next frame."""
		data = self.file.read(5) # Get the framelength from the first 5 bits
		if data: 
			framelength = int(data)
							
			# Read the current frame
			data = self.file.read(framelength)
			self.frameNum += 1
		else:
			self.restart()
			return self.nextFrame()
		return data
	
	def restart(self):
		self.file.seek(0,0)
		self.frameNum = 0
		
	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum
	
	