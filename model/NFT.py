import json


class NFT:
    tokenType = ''
    tokenId = 0
    name = ''
    imageUrl = ''
    description = ''

    def __init__(self, tokenType, tokenId, name, imageUrl, description):
        self.tokenType = tokenType
        self.tokenId = tokenId
        self.name = name
        self.imageUrl = imageUrl
        self.description = description
