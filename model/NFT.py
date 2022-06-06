import json

class NFT:
  tokenId = 0
  name = ''
  imageUrl = ''
  description = ''

  def __init__(self,tokenId, name, imageUrl, description):
    self.tokenId = tokenId
    self.name = name
    self.imageUrl = imageUrl
    self.description = description