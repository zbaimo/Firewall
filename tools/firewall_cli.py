#!/usr/bin/env python3
"""
防火墙命令行管理工具
基于iptables的完整防火墙管理
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import click
from datetime import datetime
from tabulate import tabulate
from utils.helpers import load_config
from models.database import Database
from core.firewall_enhanced import IptablesManager


# 初始化
config = load_config('config.yaml')
db = Database(config)
firewall = IptablesManager(db, config)


@click.group()
def cli():
    """🔥 Nginx防火墙 - iptables管理工具"""
    pass


# ==================== IP封禁管理 ====================

@cli.command()
@click.argument('ip')
@click.option('--reason', '-r', default='Manual ban', help='封禁原因')
@click.option('--duration', '-d', type=int, help='封禁时长（秒），不指定则永久封禁')
def ban(ip, reason, duration):
    """封禁IP地址"""
    click.echo(f"正在封禁IP: {ip}...")
    
    success = firewall.ban_ip(ip, reason, duration)
    
    if success:
        if duration:
            click.secho(f"✓ 已封禁IP: {ip} (时长: {duration}秒)", fg='green')
        else:
            click.secho(f"✓ 已永久封禁IP: {ip}", fg='green')
        click.echo(f"  原因: {reason}")
    else:
        click.secho(f"✗ 封禁失败: {ip}", fg='red')


@cli.command()
@click.argument('ip')
def unban(ip):
    """解封IP地址"""
    click.echo(f"正在解封IP: {ip}...")
    
    success = firewall.unban_ip(ip)
    
    if success:
        click.secho(f"✓ 已解封IP: {ip}", fg='green')
    else:
        click.secho(f"✗ 解封失败: {ip}", fg='red')


@cli.command()
@click.argument('ips', nargs=-1, required=True)
@click.option('--reason', '-r', default='Batch ban', help='封禁原因')
def ban_batch(ips, reason):
    """批量封禁IP"""
    click.echo(f"正在批量封禁 {len(ips)} 个IP...")
    
    results = firewall.ban_ips_batch(list(ips), reason)
    
    success_count = sum(1 for v in results.values() if v)
    
    click.echo(f"\n结果: 成功 {success_count}/{len(ips)}")
    
    for ip, success in results.items():
        status = click.style('✓', fg='green') if success else click.style('✗', fg='red')
        click.echo(f"  {status} {ip}")


@cli.command()
@click.argument('ips', nargs=-1, required=True)
def unban_batch(ips):
    """批量解封IP"""
    click.echo(f"正在批量解封 {len(ips)} 个IP...")
    
    results = firewall.unban_ips_batch(list(ips))
    
    success_count = sum(1 for v in results.values() if v)
    
    click.echo(f"\n结果: 成功 {success_count}/{len(ips)}")
    
    for ip, success in results.items():
        status = click.style('✓', fg='green') if success else click.style('✗', fg='red')
        click.echo(f"  {status} {ip}")


@cli.command()
@click.argument('ip')
def verify(ip):
    """验证IP封禁状态"""
    is_banned, details = firewall.verify_ban(ip)
    
    if is_banned:
        click.secho(f"✓ IP已被封禁: {ip}", fg='yellow')
    else:
        click.secho(f"✓ IP未被封禁: {ip}", fg='green')
    
    click.echo(f"\n详情:")
    for key, value in details.items():
        click.echo(f"  {key}: {value}")


@cli.command()
def list():
    """列出所有被封禁的IP"""
    banned_ips = firewall.list_banned_ips()
    
    if not banned_ips:
        click.echo("暂无封禁记录")
        return
    
    # 准备表格数据
    table_data = []
    for ban in banned_ips:
        table_data.append([
            ban['ip'],
            f"{ban['packets_blocked']:,}",
            f"{ban['bytes_blocked']:,}",
            ban['chain']
        ])
    
    headers = ['IP地址', '阻止包数', '阻止字节数', 'iptables链']
    
    click.echo(f"\n封禁列表 (共 {len(banned_ips)} 条):\n")
    click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))


# ==================== 端口管理 ====================

@cli.command()
@click.argument('port', type=int)
@click.option('--protocol', '-p', default='tcp', type=click.Choice(['tcp', 'udp']), help='协议')
@click.option('--source', '-s', help='来源IP（可选）')
def open_port(port, protocol, source):
    """开放端口"""
    click.echo(f"正在开放端口: {port}/{protocol}...")
    
    success = firewall.open_port(port, protocol, source)
    
    if success:
        if source:
            click.secho(f"✓ 端口已开放: {port}/{protocol} (来源: {source})", fg='green')
        else:
            click.secho(f"✓ 端口已开放: {port}/{protocol} (所有来源)", fg='green')
    else:
        click.secho(f"✗ 开放端口失败", fg='red')


@cli.command()
@click.argument('port', type=int)
@click.option('--protocol', '-p', default='tcp', type=click.Choice(['tcp', 'udp']))
def close_port(port, protocol):
    """关闭端口"""
    click.echo(f"正在关闭端口: {port}/{protocol}...")
    
    success = firewall.close_port(port, protocol)
    
    if success:
        click.secho(f"✓ 端口已关闭: {port}/{protocol}", fg='green')
    else:
        click.secho(f"✗ 关闭端口失败", fg='red')


@cli.command()
@click.argument('port', type=int)
@click.option('--protocol', '-p', default='tcp', type=click.Choice(['tcp', 'udp']))
def block_port(port, protocol):
    """阻止端口（主动拒绝）"""
    click.echo(f"正在阻止端口: {port}/{protocol}...")
    
    success = firewall.block_port(port, protocol)
    
    if success:
        click.secho(f"✓ 端口已阻止: {port}/{protocol}", fg='green')
    else:
        click.secho(f"✗ 阻止端口失败", fg='red')


# ==================== 频率限制 ====================

@cli.command()
@click.option('--limit', '-l', type=int, default=10, help='限制次数')
@click.option('--period', '-p', type=int, default=60, help='时间周期（秒）')
@click.option('--port', type=int, help='端口（可选）')
def ratelimit(limit, period, port):
    """添加频率限制规则"""
    if port:
        click.echo(f"添加频率限制: {limit}次/{period}秒 (端口: {port})")
    else:
        click.echo(f"添加频率限制: {limit}次/{period}秒 (所有端口)")
    
    success = firewall.add_rate_limit(limit, period, port)
    
    if success:
        click.secho(f"✓ 频率限制已添加", fg='green')
    else:
        click.secho(f"✗ 添加失败", fg='red')


# ==================== 统计和监控 ====================

@cli.command()
def stats():
    """显示防火墙统计信息"""
    stats = firewall.get_firewall_stats()
    
    click.echo("\n" + "="*50)
    click.secho("  防火墙统计信息", fg='cyan', bold=True)
    click.echo("="*50 + "\n")
    
    click.echo(f"总封禁数:     {stats.get('total_bans', 0):,}")
    click.echo(f"阻止数据包:   {stats.get('total_packets_blocked', 0):,}")
    click.echo(f"阻止字节数:   {stats.get('total_bytes_blocked', 0):,} bytes")
    
    chains = stats.get('chains', {})
    click.echo(f"\niptables链规则数:")
    click.echo(f"  - 封禁链:     {chains.get('bans', 0)}")
    click.echo(f"  - 频率限制:   {chains.get('rate_limits', 0)}")
    click.echo(f"  - 端口规则:   {chains.get('port_rules', 0)}")
    
    click.echo(f"\n更新时间: {stats.get('timestamp', 'N/A')}")
    click.echo("="*50 + "\n")


@cli.command()
def health():
    """防火墙健康检查"""
    click.echo("正在进行健康检查...\n")
    
    is_healthy, checks = firewall.health_check()
    
    click.echo("="*50)
    if is_healthy:
        click.secho("  ✓ 防火墙运行正常", fg='green', bold=True)
    else:
        click.secho("  ✗ 防火墙存在问题", fg='red', bold=True)
    click.echo("="*50 + "\n")
    
    click.echo("检查项:")
    for check, status in checks.items():
        status_icon = click.style('✓', fg='green') if status else click.style('✗', fg='red')
        status_value = status if isinstance(status, (int, str)) else ('通过' if status else '失败')
        click.echo(f"  {status_icon} {check}: {status_value}")


# ==================== 规则管理 ====================

@cli.command()
@click.option('--filepath', '-f', default='/etc/iptables/rules.v4', help='保存路径')
def save(filepath):
    """保存iptables规则到文件"""
    click.echo(f"正在保存规则到: {filepath}...")
    
    success = firewall.save_rules(filepath)
    
    if success:
        click.secho(f"✓ 规则已保存", fg='green')
    else:
        click.secho(f"✗ 保存失败", fg='red')


@cli.command()
@click.option('--filepath', '-f', default='/etc/iptables/rules.v4', help='规则文件路径')
@click.confirmation_option(prompt='确定要恢复规则吗？这会覆盖当前规则！')
def restore(filepath):
    """从文件恢复iptables规则"""
    click.echo(f"正在从文件恢复规则: {filepath}...")
    
    success = firewall.restore_rules(filepath)
    
    if success:
        click.secho(f"✓ 规则已恢复", fg='green')
    else:
        click.secho(f"✗ 恢复失败", fg='red')


@cli.command()
@click.option('--chain', '-c', help='链名称（可选）')
@click.confirmation_option(prompt='确定要清空规则吗？')
def flush(chain):
    """清空iptables规则"""
    if chain:
        click.echo(f"正在清空链: {chain}...")
        success = firewall.flush_chain(chain)
    else:
        click.echo(f"正在重置防火墙...")
        success = firewall.reset_firewall()
    
    if success:
        click.secho(f"✓ 清空成功", fg='green')
    else:
        click.secho(f"✗ 清空失败", fg='red')


@cli.command()
def cleanup():
    """清理过期的封禁"""
    click.echo("正在检查过期封禁...")
    
    firewall.check_expired_bans()
    
    click.secho(f"✓ 清理完成", fg='green')


# ==================== 查看规则 ====================

@cli.command()
@click.option('--chain', '-c', help='链名称（可选）')
@click.option('--verbose', '-v', is_flag=True, help='详细输出')
def show(chain, verbose):
    """显示iptables规则"""
    import subprocess
    
    if chain:
        chains = [chain]
    else:
        chains = [
            firewall.FIREWALL_CHAIN,
            firewall.RATE_LIMIT_CHAIN,
            firewall.PORT_RULES_CHAIN
        ]
    
    for chain_name in chains:
        click.echo("\n" + "="*60)
        click.secho(f"  链: {chain_name}", fg='cyan', bold=True)
        click.echo("="*60)
        
        try:
            if verbose:
                cmd = ['iptables', '-L', chain_name, '-n', '-v', '--line-numbers']
            else:
                cmd = ['iptables', '-L', chain_name, '-n', '--line-numbers']
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                click.echo(result.stdout)
            else:
                click.secho(f"  链不存在或无法访问", fg='yellow')
                
        except Exception as e:
            click.secho(f"  错误: {e}", fg='red')


# ==================== 导出功能 ====================

@cli.command()
@click.option('--output', '-o', default='firewall_export.json', help='输出文件')
def export(output):
    """导出防火墙配置"""
    import json
    
    click.echo("正在导出防火墙配置...")
    
    data = {
        'exported_at': datetime.now().isoformat(),
        'stats': firewall.get_firewall_stats(),
        'banned_ips': firewall.list_banned_ips(),
        'health': {
            'is_healthy': firewall.health_check()[0],
            'checks': firewall.health_check()[1]
        }
    }
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    click.secho(f"✓ 已导出到: {output}", fg='green')


# ==================== 快速操作 ====================

@cli.command()
@click.option('--count', '-c', type=int, default=10, help='显示数量')
def top_blocked(count):
    """显示阻止数据包最多的IP"""
    banned_ips = firewall.list_banned_ips()
    
    if not banned_ips:
        click.echo("暂无封禁记录")
        return
    
    # 按阻止包数排序
    sorted_ips = sorted(banned_ips, 
                       key=lambda x: x['packets_blocked'], 
                       reverse=True)[:count]
    
    table_data = []
    for i, ban in enumerate(sorted_ips, 1):
        table_data.append([
            i,
            ban['ip'],
            f"{ban['packets_blocked']:,}",
            f"{ban['bytes_blocked']:,}"
        ])
    
    headers = ['排名', 'IP地址', '阻止包数', '阻止字节数']
    
    click.echo(f"\nTop {count} 被阻止最多的IP:\n")
    click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))


# ==================== 交互式模式 ====================

@cli.command()
def interactive():
    """交互式管理模式"""
    click.clear()
    click.secho("="*60, fg='cyan')
    click.secho("  🔥 防火墙交互式管理", fg='cyan', bold=True)
    click.secho("="*60, fg='cyan')
    
    while True:
        click.echo("\n可用操作:")
        click.echo("  1. 封禁IP")
        click.echo("  2. 解封IP")
        click.echo("  3. 列出封禁")
        click.echo("  4. 查看统计")
        click.echo("  5. 健康检查")
        click.echo("  0. 退出")
        
        choice = click.prompt("\n请选择", type=int)
        
        if choice == 1:
            ip = click.prompt("IP地址")
            reason = click.prompt("封禁原因", default="Manual ban")
            duration = click.prompt("封禁时长（秒，0=永久）", type=int, default=0)
            
            duration_val = duration if duration > 0 else None
            success = firewall.ban_ip(ip, reason, duration_val)
            
            if success:
                click.secho(f"\n✓ 已封禁: {ip}", fg='green')
            else:
                click.secho(f"\n✗ 封禁失败", fg='red')
                
        elif choice == 2:
            ip = click.prompt("IP地址")
            success = firewall.unban_ip(ip)
            
            if success:
                click.secho(f"\n✓ 已解封: {ip}", fg='green')
            else:
                click.secho(f"\n✗ 解封失败", fg='red')
                
        elif choice == 3:
            banned_ips = firewall.list_banned_ips()
            click.echo(f"\n封禁IP数量: {len(banned_ips)}")
            for ban in banned_ips[:10]:
                click.echo(f"  - {ban['ip']} (包: {ban['packets_blocked']})")
                
        elif choice == 4:
            stats = firewall.get_firewall_stats()
            click.echo(f"\n总封禁数: {stats.get('total_bans', 0)}")
            click.echo(f"阻止包数: {stats.get('total_packets_blocked', 0):,}")
            click.echo(f"阻止字节: {stats.get('total_bytes_blocked', 0):,}")
            
        elif choice == 5:
            is_healthy, checks = firewall.health_check()
            if is_healthy:
                click.secho("\n✓ 防火墙运行正常", fg='green')
            else:
                click.secho("\n✗ 防火墙存在问题", fg='red')
            
        elif choice == 0:
            click.echo("\n再见！")
            break
        else:
            click.secho("\n无效选择", fg='red')


# ==================== 测试功能 ====================

@cli.command()
def test():
    """测试防火墙功能"""
    test_ip = "192.0.2.1"  # TEST-NET-1
    
    click.echo("="*60)
    click.secho("  防火墙功能测试", fg='cyan', bold=True)
    click.echo("="*60 + "\n")
    
    # 测试1: 健康检查
    click.echo("测试1: 健康检查...")
    is_healthy, _ = firewall.health_check()
    if is_healthy:
        click.secho("  ✓ 通过", fg='green')
    else:
        click.secho("  ✗ 失败", fg='red')
        return
    
    # 测试2: 封禁IP
    click.echo("\n测试2: 封禁IP...")
    success = firewall.ban_ip(test_ip, "测试封禁")
    if success:
        click.secho("  ✓ 通过", fg='green')
    else:
        click.secho("  ✗ 失败", fg='red')
        return
    
    # 测试3: 验证封禁
    click.echo("\n测试3: 验证封禁...")
    is_banned, _ = firewall.verify_ban(test_ip)
    if is_banned:
        click.secho("  ✓ 通过", fg='green')
    else:
        click.secho("  ✗ 失败", fg='red')
    
    # 测试4: 解封IP
    click.echo("\n测试4: 解封IP...")
    success = firewall.unban_ip(test_ip)
    if success:
        click.secho("  ✓ 通过", fg='green')
    else:
        click.secho("  ✗ 失败", fg='red')
    
    # 测试5: 验证解封
    click.echo("\n测试5: 验证解封...")
    is_banned, _ = firewall.verify_ban(test_ip)
    if not is_banned:
        click.secho("  ✓ 通过", fg='green')
    else:
        click.secho("  ✗ 失败", fg='red')
    
    click.echo("\n" + "="*60)
    click.secho("  ✓ 所有测试通过！", fg='green', bold=True)
    click.echo("="*60 + "\n")


# ==================== 主函数 ====================

if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n\n操作已取消")
        sys.exit(0)
    except Exception as e:
        click.secho(f"\n错误: {e}", fg='red')
        sys.exit(1)

