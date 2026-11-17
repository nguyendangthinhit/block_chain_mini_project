// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Lost and Found Registry
/// @notice A finder registers a found item; claimants submit claims; only the finder
///         approves one claim, which marks the item as returned. Claims on returned
///         items are rejected. All rules are enforced on-chain.
/// @dev Compile with EVM version "paris" (or "shanghai") so it runs on Ganache.
contract LostAndFoundRegistry {
    enum ItemStatus { Found, Returned }
    enum ClaimStatus { Pending, Approved }

    struct Item {
        uint256 id;
        address finder;
        string name;
        string description;
        ItemStatus status;
        uint256 approvedClaimId; // 0 while no claim is approved
        uint256 createdAt;
    }

    struct Claim {
        uint256 id;
        uint256 itemId;
        address claimant;
        string details;
        ClaimStatus status;
        uint256 createdAt;
    }

    uint256 public constant MAX_NAME_LENGTH = 64;
    uint256 public constant MAX_TEXT_LENGTH = 280;

    uint256 public itemCount;
    uint256 public claimCount;

    mapping(uint256 => Item) private items;
    mapping(uint256 => Claim) private claims;
    mapping(uint256 => uint256[]) private itemClaimIds;
    mapping(uint256 => mapping(address => bool)) public hasClaimed;

    event ItemRegistered(uint256 indexed itemId, address indexed finder, string name);
    event ClaimSubmitted(uint256 indexed claimId, uint256 indexed itemId, address indexed claimant);
    event ClaimApproved(uint256 indexed claimId, uint256 indexed itemId, address indexed claimant);
    event ItemReturned(uint256 indexed itemId, address indexed finder, address indexed owner);

    modifier itemExists(uint256 itemId) {
        require(itemId > 0 && itemId <= itemCount, "Item does not exist");
        _;
    }

    /// @notice Finder records a found item and its description.
    function registerItem(string calldata name, string calldata description) external returns (uint256) {
        require(bytes(name).length > 0, "Item name is required");
        require(bytes(name).length <= MAX_NAME_LENGTH, "Item name is too long");
        require(bytes(description).length > 0, "Description is required");
        require(bytes(description).length <= MAX_TEXT_LENGTH, "Description is too long");

        uint256 itemId = ++itemCount;
        items[itemId] = Item(itemId, msg.sender, name, description, ItemStatus.Found, 0, block.timestamp);
        emit ItemRegistered(itemId, msg.sender, name);
        return itemId;
    }

    /// @notice A claimant submits a claim with proof of ownership for a found item.
    function submitClaim(uint256 itemId, string calldata details) external itemExists(itemId) returns (uint256) {
        Item storage item = items[itemId];
        require(item.status == ItemStatus.Found, "Item already returned");
        require(msg.sender != item.finder, "Finder cannot claim own item");
        require(!hasClaimed[itemId][msg.sender], "Already claimed this item");
        require(bytes(details).length > 0, "Claim details are required");
        require(bytes(details).length <= MAX_TEXT_LENGTH, "Claim details are too long");

        uint256 claimId = ++claimCount;
        claims[claimId] = Claim(claimId, itemId, msg.sender, details, ClaimStatus.Pending, block.timestamp);
        itemClaimIds[itemId].push(claimId);
        hasClaimed[itemId][msg.sender] = true;
        emit ClaimSubmitted(claimId, itemId, msg.sender);
        return claimId;
    }

    /// @notice Only the item's finder approves a claim; the item is then marked returned.
    function approveClaim(uint256 claimId) external {
        require(claimId > 0 && claimId <= claimCount, "Claim does not exist");
        Claim storage claim = claims[claimId];
        Item storage item = items[claim.itemId];
        require(msg.sender == item.finder, "Only finder can approve");
        require(item.status == ItemStatus.Found, "Item already returned");

        claim.status = ClaimStatus.Approved;
        item.status = ItemStatus.Returned;
        item.approvedClaimId = claimId;
        emit ClaimApproved(claimId, item.id, claim.claimant);
        emit ItemReturned(item.id, item.finder, claim.claimant);
    }

    function getItem(uint256 itemId) external view itemExists(itemId) returns (Item memory) {
        return items[itemId];
    }

    function getClaim(uint256 claimId) external view returns (Claim memory) {
        require(claimId > 0 && claimId <= claimCount, "Claim does not exist");
        return claims[claimId];
    }

    function getItemClaimIds(uint256 itemId) external view itemExists(itemId) returns (uint256[] memory) {
        return itemClaimIds[itemId];
    }
}
