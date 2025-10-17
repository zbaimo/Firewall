"""
身份链管理模块
管理指纹的演变和关联关系
"""
import json
from datetime import datetime
from typing import List, Dict, Optional
from models.database import IdentityChain, Fingerprint, AccessLog


class IdentityChainManager:
    """
    身份链管理器
    
    核心功能：
    1. 检测相同基础指纹但行为变化的情况
    2. 创建身份链，将相关指纹归档在一起
    3. 维护身份链的演变历史
    """
    
    def __init__(self, db, config: Dict, fingerprint_gen):
        self.db = db
        self.config = config
        self.fingerprint_gen = fingerprint_gen
    
    def check_and_create_chain(self, base_hash: str, behavior_analysis: Dict) -> Optional[int]:
        """
        检查是否需要为该基础指纹创建身份链
        
        Args:
            base_hash: 基础指纹哈希
            behavior_analysis: 行为分析结果
            
        Returns:
            创建的身份链ID，如果不需要创建则返回None
        """
        if not behavior_analysis.get('should_create_chain'):
            return None
        
        session = self.db.get_session()
        try:
            # 检查该指纹是否已经属于某个身份链
            fingerprint = session.query(Fingerprint).filter(
                Fingerprint.base_hash == base_hash
            ).first()
            
            if fingerprint and fingerprint.identity_chain_id:
                # 已经在身份链中，更新该链
                return self._update_existing_chain(
                    session, 
                    fingerprint.identity_chain_id,
                    base_hash,
                    behavior_analysis
                )
            else:
                # 创建新的身份链
                return self._create_new_chain(
                    session,
                    base_hash,
                    behavior_analysis
                )
        finally:
            session.close()
    
    def _create_new_chain(self, session, base_hash: str, analysis: Dict) -> int:
        """创建新的身份链"""
        
        # 生成身份链的根哈希
        root_hash = self.fingerprint_gen.generate_identity_hash([base_hash])
        
        # 创建身份链记录
        chain = IdentityChain(
            root_hash=root_hash,
            fingerprint_count=1,
            total_visits=analysis.get('log_count', 0),
            evolution_history=json.dumps([{
                'hash': base_hash,
                'timestamp': datetime.now().isoformat(),
                'reason': analysis.get('reason'),
                'unique_behaviors': analysis.get('unique_behaviors'),
                'behavior_diversity': analysis.get('behavior_diversity')
            }]),
            description=f"身份链创建: 检测到行为演变 (多样性: {analysis.get('behavior_diversity', 0):.2f})"
        )
        session.add(chain)
        session.flush()  # 获取ID
        
        # 更新指纹记录，关联到身份链
        fingerprint = session.query(Fingerprint).filter(
            Fingerprint.base_hash == base_hash
        ).first()
        
        if fingerprint:
            fingerprint.identity_chain_id = chain.id
            fingerprint.is_identity_root = True
        else:
            # 如果指纹记录不存在，创建它
            # 从访问日志中获取信息
            log = session.query(AccessLog).filter(
                AccessLog.base_hash == base_hash
            ).first()
            
            if log:
                new_fingerprint = Fingerprint(
                    base_hash=base_hash,
                    ip=log.ip,
                    user_agent=log.user_agent,
                    first_seen=log.timestamp,
                    last_seen=log.timestamp,
                    visit_count=analysis.get('log_count', 1),
                    unique_behaviors=analysis.get('unique_behaviors', 1),
                    identity_chain_id=chain.id,
                    is_identity_root=True
                )
                session.add(new_fingerprint)
        
        # 更新相关的访问日志
        session.query(AccessLog).filter(
            AccessLog.base_hash == base_hash
        ).update({'identity_chain_id': chain.id})
        
        session.commit()
        
        return chain.id
    
    def _update_existing_chain(self, session, chain_id: int, new_hash: str, analysis: Dict) -> int:
        """更新现有的身份链"""
        
        chain = session.query(IdentityChain).filter(
            IdentityChain.id == chain_id
        ).first()
        
        if not chain:
            return None
        
        # 更新演变历史
        history = json.loads(chain.evolution_history) if chain.evolution_history else []
        history.append({
            'hash': new_hash,
            'timestamp': datetime.now().isoformat(),
            'reason': 'behavior_continued_evolution',
            'unique_behaviors': analysis.get('unique_behaviors'),
            'behavior_diversity': analysis.get('behavior_diversity')
        })
        
        # 重新生成根哈希（包含所有关联的指纹）
        all_hashes = [item['hash'] for item in history]
        new_root_hash = self.fingerprint_gen.generate_identity_hash(all_hashes)
        
        # 更新身份链
        chain.root_hash = new_root_hash
        chain.evolution_history = json.dumps(history)
        chain.fingerprint_count = len(all_hashes)
        chain.updated_at = datetime.now()
        chain.description = f"身份链更新: {len(all_hashes)}个关联指纹"
        
        session.commit()
        
        return chain.id
    
    def get_chain_info(self, chain_id: int) -> Optional[Dict]:
        """获取身份链详细信息"""
        session = self.db.get_session()
        try:
            chain = session.query(IdentityChain).filter(
                IdentityChain.id == chain_id
            ).first()
            
            if not chain:
                return None
            
            # 获取关联的所有指纹
            fingerprints = session.query(Fingerprint).filter(
                Fingerprint.identity_chain_id == chain_id
            ).all()
            
            # 获取威胁事件
            from models.database import ThreatEvent
            threats = session.query(ThreatEvent).filter(
                ThreatEvent.identity_chain_id == chain_id
            ).order_by(ThreatEvent.timestamp.desc()).limit(10).all()
            
            return {
                'id': chain.id,
                'root_hash': chain.root_hash,
                'created_at': chain.created_at.isoformat(),
                'updated_at': chain.updated_at.isoformat(),
                'fingerprint_count': chain.fingerprint_count,
                'total_visits': chain.total_visits,
                'threat_score': chain.threat_score,
                'evolution_history': json.loads(chain.evolution_history) if chain.evolution_history else [],
                'fingerprints': [{
                    'base_hash': fp.base_hash,
                    'ip': fp.ip,
                    'visit_count': fp.visit_count,
                    'first_seen': fp.first_seen.isoformat(),
                    'last_seen': fp.last_seen.isoformat()
                } for fp in fingerprints],
                'recent_threats': [{
                    'type': t.threat_type,
                    'severity': t.severity,
                    'timestamp': t.timestamp.isoformat(),
                    'description': t.description
                } for t in threats]
            }
        finally:
            session.close()
    
    def merge_chains(self, chain_id1: int, chain_id2: int) -> Optional[int]:
        """
        合并两个身份链
        用于发现两个看似不同的指纹实际上属于同一实体
        """
        session = self.db.get_session()
        try:
            chain1 = session.query(IdentityChain).get(chain_id1)
            chain2 = session.query(IdentityChain).get(chain_id2)
            
            if not chain1 or not chain2:
                return None
            
            # 合并演变历史
            history1 = json.loads(chain1.evolution_history) if chain1.evolution_history else []
            history2 = json.loads(chain2.evolution_history) if chain2.evolution_history else []
            merged_history = history1 + history2
            merged_history.sort(key=lambda x: x['timestamp'])
            
            # 生成新的根哈希
            all_hashes = [item['hash'] for item in merged_history]
            new_root_hash = self.fingerprint_gen.generate_identity_hash(all_hashes)
            
            # 更新第一个链
            chain1.root_hash = new_root_hash
            chain1.evolution_history = json.dumps(merged_history)
            chain1.fingerprint_count = len(all_hashes)
            chain1.total_visits = chain1.total_visits + chain2.total_visits
            chain1.threat_score = max(chain1.threat_score, chain2.threat_score)
            chain1.updated_at = datetime.now()
            chain1.description = f"合并身份链: {len(all_hashes)}个关联指纹"
            
            # 将第二个链的所有指纹和日志转移到第一个链
            session.query(Fingerprint).filter(
                Fingerprint.identity_chain_id == chain_id2
            ).update({'identity_chain_id': chain_id1})
            
            session.query(AccessLog).filter(
                AccessLog.identity_chain_id == chain_id2
            ).update({'identity_chain_id': chain_id1})
            
            from models.database import ThreatEvent
            session.query(ThreatEvent).filter(
                ThreatEvent.identity_chain_id == chain_id2
            ).update({'identity_chain_id': chain_id1})
            
            # 删除第二个链
            session.delete(chain2)
            
            session.commit()
            return chain1.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def list_all_chains(self, limit: int = 100) -> List[Dict]:
        """列出所有身份链（按威胁评分排序）"""
        session = self.db.get_session()
        try:
            chains = session.query(IdentityChain).order_by(
                IdentityChain.threat_score.desc()
            ).limit(limit).all()
            
            return [{
                'id': chain.id,
                'root_hash': chain.root_hash,
                'fingerprint_count': chain.fingerprint_count,
                'total_visits': chain.total_visits,
                'threat_score': chain.threat_score,
                'created_at': chain.created_at.isoformat(),
                'description': chain.description
            } for chain in chains]
        finally:
            session.close()

